"""Scraper de prueba para UpDown (updown.cl).

WooCommerce con tema Woodmart: mismo motor que La Loseta pero con clases
de tema distintas. La identidad del listing es el ID interno de
WooCommerce (ver woocommerce.post_id), no el SKU de negocio del boton de
compra, que no existe en los productos agotados.
"""

import sys
import time

from bs4 import BeautifulSoup

from src.http import fetch_html
from src.scrapers.woocommerce import post_id

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://www.updown.cl/categoria-producto/juegos-de-mesa/"


if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def fetch_page(url: str) -> str:
    return fetch_html(url)


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("div.product-grid-item.product"):
        title_tag = item.select_one(".wd-entities-title a")
        price_tag = item.select_one(".price .woocommerce-Price-amount")

        if not title_tag or not price_tag:
            continue

        price_text = price_tag.get_text(strip=True)
        price_clp = int(price_text.replace("$", "").replace(".", ""))

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
            "price_clp": price_clp,
            "in_stock": "instock" in item.get("class", []),
            "store_sku": post_id(item),
        })

    return products


def get_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    page_numbers = soup.select("ul.page-numbers a.page-numbers, ul.page-numbers span.page-numbers")
    numbers = [int(tag.get_text(strip=True)) for tag in page_numbers if tag.get_text(strip=True).isdigit()]
    return max(numbers) if numbers else 1


def fetch_all_products(base_url: str) -> list[dict]:
    first_page_html = fetch_page(base_url)
    total_pages = get_total_pages(first_page_html)
    print(f"Paginacion detectada: {total_pages} paginas\n")

    all_products = parse_products(first_page_html)

    for page in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY_SECONDS)
        page_url = f"{base_url}page/{page}/"
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
