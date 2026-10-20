"""Cliente minimo de la API de Telegram Bot: solo sendMessage.

Sin libreria de terceros (python-telegram-bot, etc.). Los comandos del bot los
recibe la API (webhook, backend/.../telegram); desde aqui solo se envian el
resumen de ofertas y los avisos.
"""

import os

import requests

API_BASE = "https://api.telegram.org"


def _token() -> str:
    return os.environ["TELEGRAM_BOT_TOKEN"]


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
