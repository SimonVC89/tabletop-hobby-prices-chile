"""Revisa comandos pendientes del bot de Telegram y los procesa.

Pensado para correr cada ~15 min via GitHub Actions (FR-T7): no hay
servidor persistente, asi que esto reemplaza al webhook/long-polling
habitual por un poll corto y periodico.

Anti-abuso (ver memoria del proyecto): si el mismo chat manda varios
comandos en la misma ventana de 15 min, solo se procesa el ultimo y se
responde una sola vez, en vez de contestar un mensaje por cada uno.
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

COMMAND_HANDLERS = {
    "/start": handle_start,
    "/stop": handle_stop,
    "/dar_de_baja": handle_dar_de_baja,
}


def main():
    conn = get_connection()
    try:
        offset = get_offset(conn)
        updates = get_updates(offset=offset + 1 if offset is not None else None)

        if not updates:
            print("Sin comandos nuevos.")
            return

        # Nos quedamos solo con el ultimo mensaje de cada chat en esta tanda.
        last_message_by_chat = {}
        max_update_id = offset or 0

        for update in updates:
            max_update_id = max(max_update_id, update["update_id"])
            message = update.get("message")
            if not message or "text" not in message:
                continue
            chat_id = str(message["chat"]["id"])
            last_message_by_chat[chat_id] = message["text"].strip().lower()

        for chat_id, text in last_message_by_chat.items():
            command = text.split()[0] if text else ""

            if command == "/ayuda":
                reply = HELP_TEXT
            elif command in COMMAND_HANDLERS:
                reply = COMMAND_HANDLERS[command](conn, chat_id)
            else:
                reply = "No entendi ese comando. Mandá /ayuda para ver las opciones."

            conn.commit()

            if reply:
                send_message(chat_id, reply)

        set_offset(conn, max_update_id)
        conn.commit()

        print(f"Procesados {len(last_message_by_chat)} chats, offset nuevo: {max_update_id}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
