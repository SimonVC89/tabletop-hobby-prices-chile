"""Reconstruccion de nombres completos a partir del slug de una URL.

Algunos temas de PrestaShop (PlanetaLoz, Aldea Juegos) truncan el nombre
visible en la tarjeta de producto con "..." cuando es muy largo, pero el
slug de la URL conserva el nombre completo (sin tildes). Aldea Juegos
ademas le agrega un codigo de barras al final del slug.
"""

import re

_LEADING_ID = re.compile(r"^\d+-+")
_TRAILING_BARCODE = re.compile(r"-\d{8,}$")


def title_from_slug(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = slug.removesuffix(".html")
    slug = _LEADING_ID.sub("", slug)
    slug = _TRAILING_BARCODE.sub("", slug)
    return slug.replace("-", " ").strip().title()
