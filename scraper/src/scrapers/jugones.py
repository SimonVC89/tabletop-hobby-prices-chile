"""Scraper de Jugones (jugones.cl).

Plataforma propia; todo el catalogo de juegos de mesa viene en una sola
pagina. Ojo: el atributo data-precio de cada tarjeta es el precio de
lista, no el actual -- el precio vigente es el texto visible del enlace
.precio (el <small> con "Antes:"/"Normal:" se ignora). Las tarjetas con
clase "reserva" son productos agotados que solo se pueden reservar.
"""

import re
import sys

from bs4 import BeautifulSoup, NavigableString

from src.http import fetch_html

BASE_URL = "https://www.jugones.cl"
CATEGORY_URL = f"{BASE_URL}/juegos-de-mesa"
_PRODUCT_ID = re.compile(r"/productos/(\d+)-")


if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def fetch_page(url: str) -> str:
    return fetch_html(url)


def current_price_text(price_tag) -> str:
    for node in price_tag.contents:
        if isinstance(node, NavigableString) and node.strip():
            return node.strip()
    return ""


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("div.producto"):
        title_tag = item.select_one("a.modelo")
        price_tag = item.select_one("a.precio")
        if not title_tag or not price_tag:
            continue

        digits = re.sub(r"[^\d]", "", current_price_text(price_tag))
        product_id = _PRODUCT_ID.search(title_tag["href"])
        if not digits or not product_id:
            continue

        img_tag = item.select_one("a.imagen img")
        labels = [s.get_text(strip=True) for s in item.select(".etiquetas .label")]

        products.append({
            "image_url": BASE_URL + img_tag["src"] if img_tag and img_tag.get("src") else None,
            "description": " · ".join(labels) or None,
            "title": title_tag.get_text(strip=True),
            "url": BASE_URL + title_tag["href"],
            "price_clp": int(digits),
            "in_stock": "reserva" not in price_tag.get("class", []),
            "store_sku": product_id.group(1),
        })

    return products


def fetch_all_products(base_url: str = CATEGORY_URL) -> list[dict]:
    return parse_products(fetch_page(base_url))


def main():
    products = fetch_all_products()

    print(f"Encontrados {len(products)} productos en total en {CATEGORY_URL}\n")
    for p in products:
        stock = "En stock" if p["in_stock"] else "Sin stock"
        print(f"[{p['store_sku']}] {p['title']} - ${p['price_clp']:,} - {stock}".replace(",", "."))


if __name__ == "__main__":
    main()
