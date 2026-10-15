"""Operaciones de base de datos para suscriptores del bot de Telegram."""

HELP_TEXT = (
    "Comandos disponibles:\n"
    "/start - suscribirte al resumen diario de ofertas\n"
    "/stop - darte de baja del resumen (podes volver a entrar con /start)\n"
    "/dar_de_baja - baja total y permanente de todo aviso. "
    "Para reactivar vas a necesitar visitar la pagina web (todavia no "
    "disponible).\n"
    "/ayuda - este mensaje"
)


def get_offset(conn) -> int | None:
    with conn.cursor() as cur:
        cur.execute("select value from telegram_bot_state where key = 'last_update_id'")
        row = cur.fetchone()
        return int(row[0]) if row else None


def set_offset(conn, update_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into telegram_bot_state (key, value)
            values ('last_update_id', %s)
            on conflict (key) do update set value = excluded.value
            """,
            (str(update_id),),
        )


def get_subscriber(conn, chat_id: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            "select chat_id, is_active, opted_out_permanently, is_blocked "
            "from telegram_subscribers where chat_id = %s",
            (chat_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "chat_id": row[0],
            "is_active": row[1],
            "opted_out_permanently": row[2],
            "is_blocked": row[3],
        }


def handle_start(conn, chat_id: str) -> str:
    subscriber = get_subscriber(conn, chat_id)

    if subscriber and subscriber["is_blocked"]:
        return None  # no se responde a chats bloqueados

    if subscriber and subscriber["opted_out_permanently"]:
        return (
            "Te diste de baja total anteriormente. Por ahora, la unica "
            "forma de volver a suscribirte es desde la pagina web (todavia "
            "no esta disponible)."
        )

    with conn.cursor() as cur:
        cur.execute(
            """
            insert into telegram_subscribers (chat_id, is_active, last_command_at)
            values (%s, true, now())
            on conflict (chat_id) do update set is_active = true, last_command_at = now()
            """,
            (chat_id,),
        )

    return "Listo, quedaste suscrito al resumen diario de ofertas. Usa /ayuda para ver mas opciones."


def handle_stop(conn, chat_id: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into telegram_subscribers (chat_id, is_active, last_command_at)
            values (%s, false, now())
            on conflict (chat_id) do update set is_active = false, last_command_at = now()
            """,
            (chat_id,),
        )
    return "Listo, te diste de baja del resumen diario. Podes volver a suscribirte cuando quieras con /start."


def handle_dar_de_baja(conn, chat_id: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into telegram_subscribers (chat_id, is_active, opted_out_permanently, last_command_at)
            values (%s, false, true, now())
            on conflict (chat_id) do update set
                is_active = false,
                opted_out_permanently = true,
                last_command_at = now()
            """,
            (chat_id,),
        )
    return (
        "Listo, diste de baja total: no vas a recibir ningun aviso mas. "
        "Para volver a activarlo en el futuro vas a necesitar hacerlo desde "
        "la pagina web."
    )


def mark_blocked_by_user(conn, chat_id: str):
    """El usuario bloqueo el bot en Telegram (sendMessage devolvio 403)."""
    with conn.cursor() as cur:
        cur.execute(
            "update telegram_subscribers set is_active = false where chat_id = %s",
            (chat_id,),
        )


def get_active_subscribers(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select chat_id from telegram_subscribers
            where is_active and not opted_out_permanently and not is_blocked
            """
        )
        return [row[0] for row in cur.fetchall()]
