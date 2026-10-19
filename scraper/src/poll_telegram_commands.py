"""Revisa comandos pendientes del bot de Telegram y los procesa.

Pensado para correr cada ~15 min via GitHub Actions (FR-T7): no hay
servidor persistente, asi que esto reemplaza al webhook/long-polling
habitual por un poll corto y periodico.

Anti-abuso (ver memoria del proyecto): de cada chat se procesan como maximo los
ultimos MAX_COMMANDS_PER_CHAT comandos de la tanda; el resto se descarta sin
responder. Las respuestas de un mismo chat salen juntas en un solo mensaje.
"""

from src.db import get_connection
from src.telegram import get_updates, send_message
from src.telegram_subscribers import (
    HELP_TEXT,
    get_offset,
    handle_dar_de_baja,
    handle_start,
    handle_stop,
    set_offset,
)
from src.telegram_watchlist import (
    handle_dejar_code,
    handle_mas,
    handle_seguir,
    handle_seguir_code,
    handle_siguiendo,
)

MAX_COMMANDS_PER_CHAT = 5

COMMAND_HANDLERS = {
    "/start": handle_start,
    "/stop": handle_stop,
    "/dar_de_baja": handle_dar_de_baja,
    "/siguiendo": handle_siguiendo,
}


def reply_to(conn, chat_id: str, text: str) -> str | None:
    """Respuesta a un comando, o None si no hay que responder."""
    command, _, args = text.partition(" ")
    # En grupos Telegram agrega el nombre del bot: "/seguir@MiBot catan".
    command = command.split("@")[0]

    if command == "/ayuda":
        return HELP_TEXT
    if command in COMMAND_HANDLERS:
        return COMMAND_HANDLERS[command](conn, chat_id)
    if command == "/seguir":
        return handle_seguir(conn, chat_id, args)
    if command.startswith("/seguir_"):
        return handle_seguir_code(conn, chat_id, command.removeprefix("/seguir_"))
    if command.startswith("/mas_"):
        return handle_mas(conn, chat_id, command.removeprefix("/mas_"))
    if command.startswith("/dejar_"):
        return handle_dejar_code(conn, chat_id, command.removeprefix("/dejar_"))
    return "No entendí ese comando. Envía /ayuda para ver las opciones."


def main():
    conn = get_connection()
    try:
        offset = get_offset(conn)
        updates = get_updates(offset=offset + 1 if offset is not None else None)

        if not updates:
            print("Sin comandos nuevos.")
            return

        messages_by_chat: dict[str, list[str]] = {}
        max_update_id = offset or 0

        for update in updates:
            max_update_id = max(max_update_id, update["update_id"])
            message = update.get("message")
            if not message or "text" not in message:
                continue
            chat_id = str(message["chat"]["id"])
            messages_by_chat.setdefault(chat_id, []).append(message["text"].strip().lower())

        for chat_id, texts in messages_by_chat.items():
            replies = []
            for text in texts[-MAX_COMMANDS_PER_CHAT:]:
                if text:
                    replies.append(reply_to(conn, chat_id, text))
            conn.commit()

            reply = "\n\n".join(r for r in replies if r)
            if reply:
                send_message(chat_id, reply)

        set_offset(conn, max_update_id)
        conn.commit()

        print(f"Procesados {len(messages_by_chat)} chats, offset nuevo: {max_update_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
