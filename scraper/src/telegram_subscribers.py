"""Suscriptores del bot de Telegram, para el envio del resumen.

Los comandos (/start, /stop, /dar_de_baja...) los responde la API por webhook
(backend/.../telegram/BotCommands.java); aqui solo queda lo que usa el resumen.
"""


def mark_blocked_by_user(conn, chat_id: str):
    """El usuario bloqueo el bot en Telegram (sendMessage devolvio 403).

    Se apaga el resumen y se borra su lista: si no, cada corrida seguiria
    intentando avisarle de sus juegos y recibiendo el mismo 403."""
    with conn.cursor() as cur:
        cur.execute(
            "update telegram_subscribers set is_active = false where chat_id = %s",
            (chat_id,),
        )
        cur.execute("delete from telegram_watchlist where chat_id = %s", (chat_id,))


def get_active_subscribers(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select chat_id from telegram_subscribers
            where is_active and not opted_out_permanently and not is_blocked
            """
        )
        return [row[0] for row in cur.fetchall()]
