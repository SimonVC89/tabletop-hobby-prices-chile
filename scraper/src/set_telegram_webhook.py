"""Registra (o quita) el webhook del bot de Telegram en la API publicada.

    python -m src.set_telegram_webhook            # registra el webhook
    python -m src.set_telegram_webhook --estado   # solo muestra el estado actual
    python -m src.set_telegram_webhook --borrar   # lo quita (vuelve a funcionar getUpdates)

Se corre a mano al cambiar la URL o el secreto; no forma parte del cron. Lee
TELEGRAM_BOT_TOKEN y TELEGRAM_WEBHOOK_SECRET de scraper/.env (el secreto debe ser el
mismo que tiene la API en Render). Nunca imprime ninguno de los dos.

- secret_token: Telegram lo manda en cada llamada (header
  X-Telegram-Bot-Api-Secret-Token) y la API rechaza las que no lo traen.
- max_connections=1: los mensajes llegan de a uno y en orden, asi el control de
  repetidos por update_id (que solo acepta ids crecientes) no descarta ninguno.
- allowed_updates=["message"]: el bot solo responde mensajes de texto.
"""

import argparse
import os

import requests
from dotenv import load_dotenv

API_BASE = "https://api.telegram.org"
WEBHOOK_URL = "https://thpc-api.onrender.com/api/telegram/webhook"


def call(token: str, method: str, **payload) -> dict:
    response = requests.post(f"{API_BASE}/bot{token}/{method}", json=payload, timeout=20)
    result = response.json()
    if not result.get("ok"):
        # Sin el token: la respuesta de Telegram no lo incluye.
        raise SystemExit(f"{method} fallo: {result.get('description')}")
    return result


def show_status(token: str):
    info = call(token, "getWebhookInfo")["result"]
    print(f"URL: {info.get('url') or '(sin webhook: el bot funciona con getUpdates)'}")
    print(f"Mensajes pendientes: {info.get('pending_update_count', 0)}")
    if info.get("last_error_message"):
        print(f"Ultimo error de Telegram al llamar al webhook: {info['last_error_message']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--estado", action="store_true", help="solo muestra el estado del webhook")
    group.add_argument("--borrar", action="store_true", help="quita el webhook (vuelve el polling)")
    args = parser.parse_args()

    load_dotenv(".env")
    token = os.environ["TELEGRAM_BOT_TOKEN"]

    if args.borrar:
        call(token, "deleteWebhook", drop_pending_updates=False)
        print("Webhook quitado.")
    elif not args.estado:
        call(
            token,
            "setWebhook",
            url=WEBHOOK_URL,
            secret_token=os.environ["TELEGRAM_WEBHOOK_SECRET"],
            max_connections=1,
            allowed_updates=["message"],
            # Los mensajes que llegaron mientras se cambiaba se entregan igual al webhook.
            drop_pending_updates=False,
        )
        print("Webhook registrado.")
    show_status(token)


if __name__ == "__main__":
    main()
