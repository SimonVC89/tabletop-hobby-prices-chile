"""Scraper de Diverti (diverti.cl).

PrestaShop, mismo patron general que dementegames.py / aldeajuegos.py.
El precio viene como texto ("$ 31.990") y el stock se indica con el
texto "Agotado!" dentro de un bloque .ago de cada tarjeta.
"""

import re
import sys
import time

from bs4 import BeautifulSoup

from src.http import fetch_html

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://www.diverti.cl/juegos-de-mesa-16"


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

        stock_tag = item.select_one(".ago")
        in_stock = not (stock_tag and "agotado" in stock_tag.get_text(strip=True).lower())

        img_tag = item.find("img")
        image_url = None
        description = None
        if img_tag:
            image_url = img_tag.get("data-src") or img_tag.get("src")
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url
            description = img_tag.get("alt")

        products.append({
            "image_url": image_url,
            "description": description,
            "title": title_tag.get_text(strip=True),
            "url": title_tag["href"],
            "price_clp": int(digits),
            "in_stock": in_stock,
            "store_sku": item.get("data-id-product"),
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
        html = fetch_page(f"{base_url}?page={page}")
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
