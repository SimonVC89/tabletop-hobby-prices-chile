"""Scraper de prueba para VuduGaming (vudugaming.cl).

Plataforma Jumpseller, nueva para el proyecto (distinta de WooCommerce y
PrestaShop que ya cubrimos). No se detecto una marca de "agotado" clara
en el HTML de listado durante la inspeccion inicial (ningun producto
agotado visible en esa muestra), asi que in_stock asume True salvo que
se detecte el texto "Agotado" en las etiquetas del producto.
"""

import sys
import time

from bs4 import BeautifulSoup

from src.http import fetch_html

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://www.vudugaming.cl/juegos-de-mesa"


if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def fetch_page(url: str) -> str:
    return fetch_html(url)


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("article.product-block"):
        title_tag = item.select_one(".product-block__name")
        price_tag = item.select_one(".product-block__price")
        product_id = item.get("data-product-id")

        if not title_tag or not price_tag:
            continue

        price_text = price_tag.get_text(strip=True)
        price_clp = int(price_text.replace("$", "").replace(".", ""))

        in_stock = "agotado" not in item.get_text(strip=True).lower()

        products.append({
            "title": title_tag.get_text(strip=True),
            "url": "https://www.vudugaming.cl" + title_tag["href"],
            "price_clp": price_clp,
            "in_stock": in_stock,
            "store_sku": product_id,
        })

    return products


def get_total_pages(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    last_link = soup.select_one("ul.pager li.last a")
    if last_link and "page=" in last_link["href"]:
        return int(last_link["href"].split("page=")[-1])
    return 1


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
