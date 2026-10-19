"""Normalizacion de titulos para generar una clave de matching deterministica.

La clave se arma sacando tildes/puntuacion, pasando a minusculas, sacando
palabras que son puro ruido de tienda (no distinguen el producto), y
ordenando las palabras restantes alfabeticamente para que el orden en el
titulo no importe.
"""

import re
import unicodedata

# Palabras que las tiendas agregan al nombre sin que distingan el producto:
# idioma ("Unmatched ... ESP" vs "... Español") y "Base" ("Catan" vs
# "Catan Base"). El idioma se ignora a proposito: el producto agrupa
# ediciones en distintos idiomas.
NOISE_WORDS = {"español", "espanol", "ingles", "english", "esp", "base"}
NOISE_PHRASES = re.compile(r"\bjuego de mesa\b")


# Formas distintas de escribir lo mismo (las usan el detector de duplicados y la
# busqueda del bot). Los ordinales van a un token propio ("ord2") y no a "2":
# "Machi Koro 2da Edicion" y "Machi Koro 2" son juegos distintos (el segundo es
# una secuela).
SYNONYMS = {
    "primera": "ord1", "segunda": "ord2", "tercera": "ord3", "cuarta": "ord4",
    "exp": "expansion", "ampliacion": "expansion",
    "jug": "jugadores", "ed": "edicion",
}
# "2da", "2a", "3ra", "3era", "2o" (el º queda como "o" al quitar tildes) -> "ord2", "ord3".
ORDINAL = re.compile(r"^(\d+)(?:da|ra|ta|na|ma|va|era|a|o)$")


def canonical(word: str) -> str:
    """Forma canonica de una palabra ya normalizada (sin tildes, en minusculas)."""
    m = ORDINAL.match(word)
    return f"ord{m.group(1)}" if m else SYNONYMS.get(word, word)


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def build_match_key(title: str) -> str:
    text = strip_accents(title).lower()
    text = NOISE_PHRASES.sub(" ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = [w for w in text.split() if w and w not in NOISE_WORDS]
    return " ".join(sorted(words))
