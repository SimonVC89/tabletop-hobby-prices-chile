"""Avisa por Telegram, solo al mantenedor, que una tienda manual esta por vencer.

    python -m src.alert_manual_stores               # avisa si corresponde
    python -m src.alert_manual_stores --dry-run     # muestra que mandaria, sin enviar ni guardar

Corre junto con el polling del bot (programado cada 15 min, pero en la practica
GitHub lo ejecuta cada ~3 h: el aviso de "2 horas antes" puede llegar tarde). Por cada tienda de
manual_stores calcula cuanto falta para que se cumpla el plazo en que sus
listings pasan a inactivos (STALE_AFTER_DAYS desde la ultima vez que se
scrapeo) y manda un aviso cuando faltan 24, 12 y 2 horas.

- Un solo mensaje por chequeo: si el chequeo se atrasa y ya vencieron varios
  umbrales, se manda el mas urgente y los demas se dan por avisados.
- Si el envio falla no se guarda nada, asi que el proximo chequeo reintenta.
- Cuando la tienda se actualiza, su ultima fecha cambia y se reinicia solo.
"""

import argparse
from datetime import datetime, timedelta, timezone

from src.db import get_connection
from src.manual_stores import MANUAL_ONLY_STORES
from src.mark_stale_listings import STALE_AFTER_DAYS
from src.telegram import send_message

ALERT_HOURS_BEFORE = (24, 12, 2)
STALE_AFTER = timedelta(days=STALE_AFTER_DAYS)


def get_maintainers(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "select chat_id from telegram_subscribers "
            "where is_maintainer and not opted_out_permanently and not is_blocked"
        )
        return [row[0] for row in cur.fetchall()]


def store_status(conn, store_name: str):
    """(id, ultima vez scrapeada, listings activos) de una tienda, o None si no tiene datos."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select s.id, max(pl.last_seen_at), count(*) filter (where pl.is_active)
            from stores s join product_listings pl on pl.store_id = s.id
            where s.name = %s and s.active
            group by s.id
            """,
            (store_name,),
        )
        row = cur.fetchone()
    return row if row and row[1] else None


def already_sent(conn, store_id, last_seen_at) -> set[int]:
    with conn.cursor() as cur:
        cur.execute(
            "select hours_left from maintenance_alerts where store_id = %s and last_seen_at = %s",
            (store_id, last_seen_at),
        )
        return {row[0] for row in cur.fetchall()}


def due_thresholds(time_left: timedelta) -> list[int]:
    """Umbrales (horas que faltaban) que ya se alcanzaron, del mas lejano al mas cercano."""
    return [h for h in ALERT_HOURS_BEFORE if time_left <= timedelta(hours=h)]


def build_message(store: str, hours_since: float, hours_left: float, active_listings: int) -> str:
    if hours_left > 0:
        headline = (
            f"⚠️ {store} lleva {hours_since:.0f} h sin actualizarse. "
            f"Faltan ~{hours_left:.0f} h para que sus {active_listings:,} productos dejen de contar "
            f"en ofertas y medianas.".replace(",", ".")
        )
    else:
        headline = (
            f"🚨 {store} lleva {hours_since:.0f} h sin actualizarse: ya paso el plazo. "
            f"Sus {active_listings:,} productos se marcan inactivos en la proxima corrida del cron "
            f"de la manana.".replace(",", ".")
        )
    return (
        f"{headline}\n\n"
        "Actualizala desde tu PC:\n"
        "cd scraper\n"
        f"python -m src.ingest_{store.lower()}"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="no envia ni guarda nada")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    conn = get_connection()
    try:
        maintainers = get_maintainers(conn)
        for store in sorted(MANUAL_ONLY_STORES):
            status = store_status(conn, store)
            if not status:
                print(f"{store}: sin datos, se omite")
                continue
            store_id, last_seen_at, active_listings = status

            time_left = last_seen_at + STALE_AFTER - now
            hours_since = (now - last_seen_at).total_seconds() / 3600
            hours_left = time_left.total_seconds() / 3600
            pending = [h for h in due_thresholds(time_left) if h not in already_sent(conn, store_id, last_seen_at)]

            print(f"{store}: {hours_since:.1f} h sin actualizar, faltan {hours_left:.1f} h | umbrales pendientes: {pending or 'ninguno'}")
            if not pending:
                continue

            text = build_message(store, hours_since, hours_left, active_listings)
            if args.dry_run:
                print(f"--- mensaje (no enviado) a {len(maintainers)} mantenedor(es):\n{text}")
                continue
            if not maintainers:
                print("Hay un aviso pendiente pero no hay ningun mantenedor activo: no se envia ni se guarda.")
                continue

            sent = [chat for chat in maintainers if send_message(chat, text).get("ok")]
            if not sent:
                print("No se pudo enviar a ningun mantenedor, se reintenta en el proximo chequeo.")
                continue
            with conn.cursor() as cur:
                for h in pending:
                    cur.execute(
                        "insert into maintenance_alerts (store_id, last_seen_at, hours_left) values (%s, %s, %s) "
                        "on conflict do nothing",
                        (store_id, last_seen_at, h),
                    )
            conn.commit()
            print(f"Aviso enviado a {len(sent)} mantenedor(es); umbrales marcados: {pending}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
