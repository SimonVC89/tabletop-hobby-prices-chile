"""Scraper de prueba para La Loseta (laloseta.cl).

Etapa actual: solo parsea una pagina de categoria y muestra los productos
encontrados por consola. No guarda nada en Supabase todavia.
"""

import sys
import time

from bs4 import BeautifulSoup

from src.http import fetch_html
from src.scrapers.woocommerce import post_id

REQUEST_DELAY_SECONDS = 1.5

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

CATEGORY_URL = "https://laloseta.cl/categoria-producto/juego-de-mesa/"



def fetch_category_page(url: str) -> str:
    return fetch_html(url)


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("ul.products li.product"):
        title_tag = item.select_one(".woocommerce-loop-product__title")
        link_tag = item.select_one("a.woocommerce-loop-product__link")
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
            "url": link_tag["href"] if link_tag else None,
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
    first_page_html = fetch_category_page(base_url)
    total_pages = get_total_pages(first_page_html)
    print(f"Paginación detectada: {total_pages} páginas\n")

    all_products = parse_products(first_page_html)

    for page in range(2, total_pages + 1):
        time.sleep(REQUEST_DELAY_SECONDS)
        page_url = f"{base_url}page/{page}/"
        html = fetch_category_page(page_url)
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
