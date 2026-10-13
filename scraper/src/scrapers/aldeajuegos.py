"""Scraper de prueba para Aldea Juegos (aldeajuegos.cl).

PrestaShop, mismo patron general que dementegames.py / planetaloz.py,
pero el precio viene como texto "$ 47.588" (con espacio, sin atributo
content limpio).
"""

import re
import sys
import time

from bs4 import BeautifulSoup

from src.http import fetch_html
from src.slug import title_from_slug

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://www.aldeajuegos.cl/7-juegos-de-mesa"


if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def fetch_page(url: str) -> str:
    return fetch_html(url)


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("article.product-miniature"):
        title_tag = item.select_one(".product-title a")
        price_tag = item.select_one(".price")

        if not title_tag or not price_tag:
            continue

        digits = re.sub(r"[^\d]", "", price_tag.get_text(strip=True))
        if not digits:
            continue

        title = title_tag.get_text(strip=True)
        if title.endswith("..."):
            title = title_from_slug(title_tag["href"])

        products.append({
            "title": title,
            "url": title_tag["href"],
            "price_clp": int(digits),
            "in_stock": True,
            "store_sku": item.get("data-id-product"),
        })

    return products


def get_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    page_links = soup.select("ul.page-list a")
    numbers = [int(a.get_text(strip=True)) for a in page_links if a.get_text(strip=True).isdigit()]
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
