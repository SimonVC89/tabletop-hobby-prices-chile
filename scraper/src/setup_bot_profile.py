"""Configura el perfil publico del bot de Telegram: descripcion, descripcion corta y menu de comandos.

    python -m src.setup_bot_profile             # aplica los textos
    python -m src.setup_bot_profile --dry-run   # solo los muestra y valida los limites

Se corre a mano cuando cambian estos textos; no forma parte del cron.

La descripcion es lo primero que se ve: Telegram la muestra en el chat vacio, ANTES de
que la persona toque "Iniciar". El menu de comandos es lo que aparece al escribir "/",
y sirve de autocompletado de los nombres de comando. Desde que la API recibe los
mensajes por webhook las respuestas son inmediatas, asi que ya no hay aviso de demora.
"""

import argparse
import os
import re

import requests
from dotenv import load_dotenv

API_BASE = "https://api.telegram.org"

# Limites de la Bot API: descripcion 512, descripcion corta 120, comando 32 / su texto 256.
DESCRIPTION_MAX = 512
SHORT_DESCRIPTION_MAX = 120

DESCRIPTION = (
    "Te aviso cuando un juego de mesa baja de precio en tiendas chilenas, y sigo los juegos que tú "
    "elijas con /seguir.\n\n"
    "Recibes un resumen en la mañana y en la tarde, solo cuando hay ofertas nuevas, y un aviso cuando "
    "un juego que sigues baja de precio o vuelve a tener stock.\n\n"
    "Toca Iniciar para empezar."
)
SHORT_DESCRIPTION = "Ofertas de juegos de mesa en Chile y aviso cuando bajan los juegos que sigues."

COMMANDS = [
    ("start", "Recibir el resumen de ofertas"),
    ("seguir", "Seguir un juego, por ejemplo: /seguir catan"),
    ("siguiendo", "Ver los juegos que sigues"),
    ("stop", "Pausar el resumen de ofertas"),
    ("dar_de_baja", "Baja total y permanente de todo aviso"),
    ("ayuda", "Ver los comandos y cómo funciona"),
]


def validate():
    """Falla antes de llamar a Telegram si algun texto supera sus limites."""
    assert len(DESCRIPTION) <= DESCRIPTION_MAX, f"descripcion de {len(DESCRIPTION)} caracteres (max {DESCRIPTION_MAX})"
    assert len(SHORT_DESCRIPTION) <= SHORT_DESCRIPTION_MAX, (
        f"descripcion corta de {len(SHORT_DESCRIPTION)} caracteres (max {SHORT_DESCRIPTION_MAX})"
    )
    for name, text in COMMANDS:
        assert re.fullmatch(r"[a-z0-9_]{1,32}", name), f"comando invalido: {name}"
        assert 3 <= len(text) <= 256, f"texto del comando {name} fuera de rango"


def call(token: str, method: str, **payload) -> dict:
    response = requests.post(f"{API_BASE}/bot{token}/{method}", json=payload, timeout=20)
    result = response.json()
    if not result.get("ok"):
        raise SystemExit(f"{method} fallo: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="muestra los textos sin enviarlos")
    args = parser.parse_args()

    validate()
    print(f"Descripcion ({len(DESCRIPTION)}/{DESCRIPTION_MAX}):\n{DESCRIPTION}\n")
    print(f"Descripcion corta ({len(SHORT_DESCRIPTION)}/{SHORT_DESCRIPTION_MAX}): {SHORT_DESCRIPTION}\n")
    print("Comandos:\n" + "\n".join(f"  /{name} - {text}" for name, text in COMMANDS))
    if args.dry_run:
        print("\n(SIMULACION: no se envio nada a Telegram)")
        return

    load_dotenv(".env")
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    call(token, "setMyDescription", description=DESCRIPTION)
    call(token, "setMyShortDescription", short_description=SHORT_DESCRIPTION)
    call(token, "setMyCommands", commands=[{"command": n, "description": t} for n, t in COMMANDS])
    print("\nPerfil del bot actualizado.")


if __name__ == "__main__":
    main()
