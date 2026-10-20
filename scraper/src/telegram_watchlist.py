"""Avisos de los juegos que cada chat sigue por Telegram.

Los comandos para seguir juegos (/seguir, /siguiendo, /dejar...) y su busqueda los
responde la API por webhook (backend/.../telegram). Aqui quedan los avisos, que
manda send_telegram_digest tras cada corrida de scraping:
- el mejor precio con stock baja al menos WATCH_DROP_PCT% bajo el nivel de
  referencia (el precio al seguir o el de la ultima vez que se aviso);
- un juego que estaba agotado vuelve a tener stock.
No se avisa cuando el precio sube ni cuando se agota; el nivel de referencia solo
se mueve en los avisos, asi dos bajadas chicas seguidas no se pierden.
"""

# El mismo umbral usa la API al confirmar un /seguir (BotTexts.WATCH_DROP_PCT).
WATCH_DROP_PCT = 5


def clp(value: int) -> str:
    return "$" + f"{value:,}".replace(",", ".")


def decide(prev_in_stock: bool, ref_price: int | None, best: int | None) -> tuple[str | None, int | None, bool]:
    """Que pasa con un juego seguido en esta revision.

    Devuelve (evento, nuevo nivel de referencia, nuevo estado de stock). El evento
    es "restock", "drop" o None. Ver el docstring del modulo para las reglas.
    """
    if best is None:
        return None, ref_price, False  # se agoto: sin aviso, se recuerda para detectar el regreso
    if not prev_in_stock or ref_price is None:
        return "restock", best, True
    if best <= ref_price * (1 - WATCH_DROP_PCT / 100):
        return "drop", best, True
    return None, ref_price, True


def collect_alerts(conn) -> tuple[list[dict], list[dict]]:
    """Revisa todos los juegos seguidos. Devuelve (avisos, cambios silenciosos).

    Un aviso lleva el estado nuevo (new_ref / new_in_stock) que solo debe guardarse
    cuando el mensaje se envio bien; un cambio silencioso (se agoto) se guarda ya.
    Solo considera chats que pueden recibir mensajes (sin baja total ni bloqueo).
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            select w.chat_id, w.product_id::text, p.canonical_name, w.ref_price, w.in_stock,
                   b.price_clp, b.store_name, b.url
            from telegram_watchlist w
            join telegram_subscribers t on t.chat_id = w.chat_id
            join products p on p.id = w.product_id
            left join lateral (
                select cp.price_clp, s.name as store_name, pl.url
                from current_prices cp
                join stores s on s.id = cp.store_id
                join product_listings pl on pl.id = cp.listing_id
                where cp.product_id = w.product_id and cp.in_stock
                order by cp.price_clp limit 1
            ) b on true
            where not t.opted_out_permanently and not t.is_blocked
            """
        )
        rows = cur.fetchall()

    alerts, silent = [], []
    for chat_id, product_id, name, ref_price, in_stock, best, store, url in rows:
        event, new_ref, new_in_stock = decide(in_stock, ref_price, best)
        if event:
            alerts.append({
                "chat_id": chat_id, "product_id": product_id, "name": name, "event": event,
                "price": best, "previous": ref_price, "store": store, "url": url,
                "new_ref": new_ref, "new_in_stock": new_in_stock,
            })
        elif (new_ref, new_in_stock) != (ref_price, in_stock):
            silent.append({"chat_id": chat_id, "product_id": product_id, "new_ref": new_ref, "new_in_stock": new_in_stock})
    return alerts, silent


def save_state(conn, changes: list[dict], alerted: bool):
    with conn.cursor() as cur:
        for c in changes:
            cur.execute(
                """
                update telegram_watchlist
                set ref_price = %s, in_stock = %s, last_alert_at = case when %s then now() else last_alert_at end
                where chat_id = %s and product_id = %s
                """,
                (c["new_ref"], c["new_in_stock"], alerted, c["chat_id"], c["product_id"]),
            )


def format_watch_section(alerts: list[dict]) -> str:
    lines = ["⭐ De tu lista:"]
    for a in alerts:
        if a["event"] == "drop":
            drop = round(100 * (a["previous"] - a["price"]) / a["previous"])
            what = f"bajó a {clp(a['price'])} en {a['store']} (antes {clp(a['previous'])}, -{drop}%)"
        else:
            what = f"volvió a tener stock desde {clp(a['price'])} en {a['store']}"
        lines.append(f"• {a['name']} {what}\n  {a['url']}")
    return "\n".join(lines)
