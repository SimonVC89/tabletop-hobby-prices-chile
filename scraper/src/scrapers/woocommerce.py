"""Utilidades compartidas por los scrapers de tiendas WooCommerce."""

import re

_POST_ID = re.compile(r"post-(\d+)")


def post_id(item) -> str | None:
    """ID interno del producto, desde la clase "post-NNN" de su contenedor.

    Esta en todos los productos del listado, con o sin stock. No usar el
    data-product_id del boton "Anadir al carrito": los productos agotados
    no tienen ese boton, y un SKU vacio rompe el upsert (NULL no choca con
    la restriccion UNIQUE y se inserta una fila nueva en cada corrida).
    """
    for cls in item.get("class", []):
        match = _POST_ID.fullmatch(cls)
        if match:
            return match.group(1)
    return None
