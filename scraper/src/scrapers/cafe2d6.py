"""Scraper de prueba para Cafe 2d6 / Dos de Seis (cafe2d6.cl).

Shopify, tema propio. No tiene una coleccion unica "juegos-de-mesa"
(el catalogo esta repartido en subcolecciones tematicas), asi que se usa
/collections/all. El precio puede venir con un precio tachado al lado
(oferta), por eso se toma solo el primer nodo de texto del <p class="price">.
"""

import re
import sys
import time

import requests
from bs4 import BeautifulSoup, NavigableString

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://www.cafe2d6.cl/collections/all"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def first_price_text(price_tag) -> str:
    for node in price_tag.contents:
        if isinstance(node, NavigableString) and node.strip():
            return node.strip()
    return price_tag.get_text(strip=True)


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("li.item.itemqt"):
        title_tag = item.select_one(".text h3")
        price_tag = item.select_one(".price")
        link_tag = item.select_one("a[href]")

        if not title_tag or not price_tag or not link_tag:
            continue

        digits = re.sub(r"[^\d]", "", first_price_text(price_tag))
        if not digits:
            continue

        products.append({
            "title": title_tag.get_text(strip=True),
            "url": "https://www.cafe2d6.cl" + link_tag["href"],
            "price_clp": int(digits),
            "in_stock": True,
            "store_sku": item.get("data-id"),
        })

    return products


def get_total_pages(html: str) -> int:
    numbers = [int(m) for m in re.findall(r"[?&]page=(\d+)", html)]
    return max(numbers) if numbers else 1


def fetch_all_products(base_url: str) -> list[dict]:
    first_page_html = fetch_page(base_url)
    total_pages = get_total_pages(first_page_html)
    print(f"Paginacion detectada: {total_pages} paginas\n")

    all_products = parse_products(first_page_html)

    for page in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY_SECONDS)
        page_url = f"{base_url}?page={page}"
        html = fetch_page(page_url)
        all_products.extend(parse_products(html))

    return all_products


def main():
    products = fetch_all_products(CATEGORY_URL)

    print(f"Encontrados {len(products)} productos en total en {CATEGORY_URL}\n")
    for p in products:
        stock = "En stock" if p["in_stock"] else "Sin stock"
        print(f"[{p['store_sku']}] {p['title']} - ${p['price_clp']:,} - {stock}".replace(",", "."))


if __name__ == "__main__":
    main()
