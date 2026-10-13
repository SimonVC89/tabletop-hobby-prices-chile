"""Normalizacion de titulos para generar una clave de matching deterministica.

La clave se arma sacando tildes/puntuacion, pasando a minusculas, sacando
palabras que son puro ruido de tienda (no distinguen el producto), y
ordenando las palabras restantes alfabeticamente para que el orden en el
titulo no importe.
"""

import re
import unicodedata

NOISE_WORDS = {"español", "espanol", "ingles", "english"}


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def build_match_key(title: str) -> str:
    text = strip_accents(title).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [w for w in text.split() if w and w not in NOISE_WORDS]
    return " ".join(sorted(words))
