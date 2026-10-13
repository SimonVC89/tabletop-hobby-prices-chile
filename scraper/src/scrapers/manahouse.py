"""Scraper de prueba para Mana House (manahouse.cl).

Shopify, tema propio: contenedor div.product-grid-item, con clase
"soldout" en el contenedor cuando no hay stock.
"""

import re
import sys
import time

import requests
from bs4 import BeautifulSoup

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://manahouse.cl/collections/juegos-de-mesa"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("div.product-grid-item"):
        title_tag = item.select_one(".product-grid-item__title")
        price_tag = item.select_one(".product-grid-item__price")

        if not title_tag or not price_tag:
            continue

        digits = re.sub(r"[^\d]", "", price_tag.get_text(strip=True))
        if not digits:
            continue

        url = title_tag["href"]
        slug = url.rstrip("/").rsplit("/", 1)[-1]

        products.append({
            "title": title_tag.get_text(strip=True),
            "url": "https://manahouse.cl" + url,
            "price_clp": int(digits),
            "in_stock": "soldout" not in item.get("class", []),
            "store_sku": slug,
        })

    return products


def get_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
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
