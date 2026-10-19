"""Arma y manda el resumen de ofertas por Telegram (FR-T4/T8/T9) y los avisos de
los juegos que cada persona sigue (/seguir, ver telegram_watchlist).

Se corre al final de cada corrida del cron (manana y tarde), despues de
refresh_price_views. Cada chat recibe como maximo un mensaje por corrida, con la
seccion "De tu lista" arriba y el resumen de ofertas despues (si esta suscrito).
Si no hay nada nuevo que contar, no manda nada: ni se marca nada en price_alerts.
"""

from collections import defaultdict

from src.db import get_connection
from src.telegram import send_message
from src.telegram_subscribers import get_active_subscribers, mark_blocked_by_user
from src.telegram_watchlist import collect_alerts, format_watch_section, save_state

TELEGRAM_MESSAGE_LIMIT = 4096
MIN_STORE_COUNT = 3
DESTACADA_THRESHOLD = 50
OFERTA_THRESHOLD = 20
TOP_N_DESTACADAS = 10
TOP_N_OTRAS = 15


def fetch_candidate_offers(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            -- Si una tienda publica el mismo juego en dos paginas, cuenta
            -- una sola vez (la mas barata), antes de filtrar lo ya avisado.
            select * from (
              select distinct on (cp.product_id, cp.store_id)
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
              order by cp.product_id, cp.store_id, cp.price_clp
            ) o
            where not exists (
                select 1 from price_alerts pa
                where pa.listing_id = o.listing_id and pa.price_clp = o.price_clp
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
        # Solo el separador de miles del precio: reemplazar comas en toda la linea
        # rompia la coma de "off, Tienda" y cualquier coma del nombre o del enlace.
        price = f"{o['price_clp']:,}".replace(",", ".")
        lines.append(
            f"{i}. {o['canonical_name']} - ${price} ({o['discount_pct']}% off, {o['store_name']})\n"
            f"   {o['url']}"
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


def greeting_for_hour(hour: int) -> str:
    """Saludo segun la hora de Chile en que SALE el mensaje, no la de la corrida
    programada: GitHub atrasa los cron varias horas (la de la manana llego a salir
    pasado el mediodia), y decir "esta manana" a la 1 pm confunde."""
    if hour < 12:
        return "☀️ Resumen de esta mañana"
    if hour < 20:
        return "🌆 Resumen de esta tarde"
    return "🌙 Resumen de esta noche"


def period_greeting(conn) -> str:
    """Encabezado segun la hora actual de Chile. La hora la da Postgres para no
    depender de tzdata (que no viene con Python en Windows)."""
    with conn.cursor() as cur:
        cur.execute("select extract(hour from now() at time zone 'America/Santiago')")
        return greeting_for_hour(int(cur.fetchone()[0]))


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


def send_parts(chat_id: str, greeting: str, parts: list[str]) -> dict:
    """Manda las secciones juntas en un mensaje; si no caben en el limite de Telegram,
    una por mensaje (con el saludo solo en el primero). Si alguna falla, devuelve ese error.

    Sin esto, un mensaje de mas de 4096 caracteres fallaria en silencio y se repetiria
    el mismo fallo en cada corrida.
    """
    text = f"{greeting}\n\n" + "\n\n".join(parts)
    messages = [text] if len(text) <= TELEGRAM_MESSAGE_LIMIT else [
        f"{greeting}\n\n{part}" if i == 0 else part for i, part in enumerate(parts)
    ]
    for message in messages:
        result = send_message(chat_id, message)
        if not result.get("ok"):
            return result
    return {"ok": True}


def main():
    conn = get_connection()
    try:
        offers = fetch_candidate_offers(conn)
        qualifying = [o for o in offers if o["discount_pct"] >= OFERTA_THRESHOLD]
        digest_body = build_digest_text(qualifying) if qualifying else None
        digest_subscribers = set(get_active_subscribers(conn)) if digest_body else set()

        # Juegos seguidos con /seguir. Lo que se agoto no avisa: se guarda de inmediato.
        # Los avisos guardan su estado nuevo solo si el mensaje salio bien.
        watch_alerts, silent_changes = collect_alerts(conn)
        save_state(conn, silent_changes, alerted=False)
        alerts_by_chat = defaultdict(list)
        for alert in watch_alerts:
            alerts_by_chat[alert["chat_id"]].append(alert)

        recipients = sorted(digest_subscribers | set(alerts_by_chat))
        if not recipients:
            conn.commit()
            if qualifying:
                print(f"{len(qualifying)} ofertas calificaron, pero no hay suscriptores activos. No se marca nada.")
            else:
                print("Sin ofertas nuevas ni novedades de juegos seguidos, no se manda nada.")
            return

        greeting = period_greeting(conn)
        digest_sent = watch_sent = 0
        for chat_id in recipients:
            parts = []
            if chat_id in alerts_by_chat:
                parts.append(format_watch_section(alerts_by_chat[chat_id]))
            if chat_id in digest_subscribers:
                parts.append(digest_body)

            result = send_parts(chat_id, greeting, parts)
            if result.get("ok"):
                digest_sent += chat_id in digest_subscribers
                if chat_id in alerts_by_chat:
                    watch_sent += len(alerts_by_chat[chat_id])
                    save_state(conn, alerts_by_chat[chat_id], alerted=True)
            elif result.get("error_code") == 403:
                print(f"Chat {chat_id} bloqueo el bot, lo marco inactivo.")
                mark_blocked_by_user(conn, chat_id)
            else:
                print(f"Error mandando a {chat_id}: {result}")

        conn.commit()

        if digest_sent > 0:
            mark_offers_as_notified(conn, qualifying)
            conn.commit()
            print(f"Resumen mandado a {digest_sent} suscriptores, {len(qualifying)} ofertas marcadas como notificadas.")
        elif digest_subscribers:
            print("No se pudo mandar el resumen a ningun suscriptor, no se marcan ofertas.")
        print(f"Avisos de juegos seguidos enviados: {watch_sent} de {len(watch_alerts)}.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
