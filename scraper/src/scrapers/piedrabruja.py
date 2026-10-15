"""Scraper de Piedra Bruja (piedrabruja.cl).

Shopify. En vez de parsear HTML usa el endpoint publico que expone toda
tienda Shopify (/collections/<coleccion>/products.json): devuelve los
mismos datos estructurados, incluida la descripcion real del producto,
con muchos menos requests (250 productos por pagina). Su robots.txt no
lo restringe (solo /recommendations/products).
"""

import json
import re
import sys
import time
from html import unescape

from src.http import fetch_html

REQUEST_DELAY_SECONDS = 1.5
BASE_URL = "https://piedrabruja.cl"
COLLECTION = "juegos-de-mesa"
CATEGORY_URL = f"{BASE_URL}/collections/{COLLECTION}"
PAGE_SIZE = 250
DESCRIPTION_MAX_CHARS = 280


if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def plain_text(html: str | None, max_chars: int) -> str | None:
    if not html:
        return None
    text = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()
    if len(text) <= max_chars:
        return text or None
    return text[:max_chars].rsplit(" ", 1)[0] + "…"


def parse_products(raw: list[dict]) -> list[dict]:
    products = []
    for p in raw:
        variants = p.get("variants") or []
        if not variants:
            continue
        price = min(int(float(v["price"])) for v in variants)
        images = p.get("images") or []

        products.append({
            "image_url": images[0]["src"] if images else None,
            "description": plain_text(p.get("body_html"), DESCRIPTION_MAX_CHARS),
            "title": p["title"].strip(),
            "url": f"{BASE_URL}/products/{p['handle']}",
            "price_clp": price,
            "in_stock": any(v.get("available") for v in variants),
            "store_sku": str(p["id"]),
        })
    return products


def fetch_all_products(collection_url: str = CATEGORY_URL) -> list[dict]:
    all_products = []
    page = 1
    while True:
        if page > 1:
            time.sleep(REQUEST_DELAY_SECONDS)
        raw = json.loads(fetch_html(f"{collection_url}/products.json?limit={PAGE_SIZE}&page={page}"))
        batch = raw.get("products", [])
        if not batch:
            break
        all_products.extend(parse_products(batch))
        page += 1
    print(f"Paginas JSON leidas: {page - 1}\n")
    return all_products


def main():
    products = fetch_all_products()

    print(f"Encontrados {len(products)} productos en total en {CATEGORY_URL}\n")
    for p in products:
        stock = "En stock" if p["in_stock"] else "Sin stock"
        print(f"[{p['store_sku']}] {p['title']} - ${p['price_clp']:,} - {stock}".replace(",", "."))


if __name__ == "__main__":
    main()
