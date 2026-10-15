"""Arma y manda el resumen diario de ofertas por Telegram (FR-T4/T8/T9).

Se corre al final del cron diario, despues de refresh_price_views. Si no
hay ninguna oferta nueva que calificar, no manda nada (ni a los
suscriptores ni se marca nada en price_alerts).
"""

from src.db import get_connection
from src.telegram import send_message
from src.telegram_subscribers import get_active_subscribers, mark_blocked_by_user

MIN_STORE_COUNT = 3
DESTACADA_THRESHOLD = 50
OFERTA_THRESHOLD = 20
TOP_N_DESTACADAS = 10
TOP_N_OTRAS = 15


def fetch_candidate_offers(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select
              cp.listing_id,
              p.canonical_name,
              s.name as store_name,
              pl.url,
              cp.price_clp,
              pps.median_price_clp,
              round((100 * (pps.median_price_clp - cp.price_clp) / pps.median_price_clp)::numeric, 1) as discount_pct
            from current_prices cp
            join product_price_stats pps on pps.product_id = cp.product_id
            join products p on p.id = cp.product_id
            join stores s on s.id = cp.store_id
            join product_listings pl on pl.id = cp.listing_id
            where pps.store_count >= %s
              and cp.in_stock
              and cp.price_clp < pps.median_price_clp
              and p.category = 'board_game'
              and not exists (
                  select 1 from price_alerts pa
                  where pa.listing_id = cp.listing_id and pa.price_clp = cp.price_clp
              )
            order by discount_pct desc
            """,
            (MIN_STORE_COUNT,),
        )
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def format_section(title: str, offers: list[dict], top_n: int) -> str:
    if not offers:
        return ""

    shown = offers[:top_n]
    remaining = len(offers) - len(shown)

    lines = [title]
    for i, o in enumerate(shown, start=1):
        lines.append(
            f"{i}. {o['canonical_name']} - ${o['price_clp']:,} ({o['discount_pct']}% off, {o['store_name']})\n"
            f"   {o['url']}".replace(",", ".")
        )

    if remaining > 0:
        lines.append(f"...y {remaining} ofertas mas.")

    return "\n".join(lines)


def build_digest_text(offers: list[dict]) -> str | None:
    destacadas = [o for o in offers if o["discount_pct"] >= DESTACADA_THRESHOLD]
    otras = [o for o in offers if OFERTA_THRESHOLD <= o["discount_pct"] < DESTACADA_THRESHOLD]

    sections = [
        format_section("🔥 Ofertas destacadas (50%+ bajo la mediana):", destacadas, TOP_N_DESTACADAS),
        format_section("💰 Otras ofertas (20%+ bajo la mediana):", otras, TOP_N_OTRAS),
    ]
    sections = [s for s in sections if s]

    if not sections:
        return None

    return "\n\n".join(sections)


def mark_offers_as_notified(conn, offers: list[dict]):
    with conn.cursor() as cur:
        for o in offers:
            cur.execute(
                """
                insert into price_alerts (listing_id, price_clp, reference_price_clp, discount_pct)
                values (%s, %s, %s, %s)
                """,
                (o["listing_id"], o["price_clp"], round(o["median_price_clp"]), o["discount_pct"]),
            )


def main():
    conn = get_connection()
    try:
        offers = fetch_candidate_offers(conn)
        qualifying = [o for o in offers if o["discount_pct"] >= OFERTA_THRESHOLD]

        if not qualifying:
            print("Sin ofertas nuevas que calificar, no se manda nada.")
            return

        text = build_digest_text(qualifying)
        subscribers = get_active_subscribers(conn)

        if not subscribers:
            print(f"{len(qualifying)} ofertas calificaron, pero no hay suscriptores activos. No se marca nada.")
            return

        sent_count = 0
        for chat_id in subscribers:
            result = send_message(chat_id, text)
            if result.get("ok"):
                sent_count += 1
            elif result.get("error_code") == 403:
                print(f"Chat {chat_id} bloqueo el bot, lo marco inactivo.")
                mark_blocked_by_user(conn, chat_id)
            else:
                print(f"Error mandando a {chat_id}: {result}")

        conn.commit()

        if sent_count > 0:
            mark_offers_as_notified(conn, qualifying)
            conn.commit()
            print(f"Digest mandado a {sent_count} suscriptores, {len(qualifying)} ofertas marcadas como notificadas.")
        else:
            print("No se pudo mandar a ningun suscriptor, no se marca nada.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
