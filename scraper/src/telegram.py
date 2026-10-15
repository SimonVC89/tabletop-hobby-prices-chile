"""Cliente minimo de la API de Telegram Bot.

Sin libreria de terceros (python-telegram-bot, etc.) porque solo
necesitamos 2 llamadas: getUpdates (polling) y sendMessage.
"""

import os

import requests

API_BASE = "https://api.telegram.org"


def _token() -> str:
    return os.environ["TELEGRAM_BOT_TOKEN"]


def get_updates(offset: int | None = None, timeout: int = 10) -> list[dict]:
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset

    response = requests.get(f"{API_BASE}/bot{_token()}/getUpdates", params=params, timeout=timeout + 10)
    response.raise_for_status()
    data = response.json()
    return data.get("result", [])


def send_message(chat_id: str, text: str) -> dict:
    """Envia un mensaje. Devuelve el JSON de respuesta de Telegram.

    No lanza excepcion en errores de Telegram (ej. 403 bot bloqueado por
    el usuario): quien llama decide que hacer con ok=False.
    """
    response = requests.post(
        f"{API_BASE}/bot{_token()}/sendMessage",
        json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
        timeout=15,
    )
    return response.json()
