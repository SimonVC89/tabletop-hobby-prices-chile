"""Scraper de prueba para PlanetaLoz (planetaloz.cl).

Tambien PrestaShop (mismo patron que dementegames.py), pero con un tema
distinto: el precio viene como texto "$ 25.000" en vez de un atributo
"content" limpio, y no se encontro una marca visible de "agotado" en el
listado, asi que in_stock queda fijo en True por ahora.
"""

import re
import sys
import time

import requests
from bs4 import BeautifulSoup

REQUEST_DELAY_SECONDS = 1.5
CATEGORY_URL = "https://www.planetaloz.cl/14-juegos-de-mesa"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


def title_from_slug(url: str) -> str:
    """Reconstruye el nombre completo desde el slug de la URL.

    PlanetaLoz trunca el nombre visible en la tarjeta de producto (ej.
    "Terraforming Mars...") pero el slug de la URL conserva el nombre
    completo, aunque sin tildes: ".../8646-terraforming-mars-automa-
    expansion.html" -> "Terraforming Mars Automa Expansion".
    """
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    slug = slug.removesuffix(".html")
    slug = re.sub(r"^\d+-+", "", slug)
    return slug.replace("-", " ").strip().title()


def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def parse_products(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("div#js-product-list article.product-miniature"):
        title_tag = item.select_one(".product-title a")
        price_tag = item.select_one("[itemprop='price']")

        if not title_tag or not price_tag:
            continue

        price_text = price_tag.get_text(strip=True)
        price_clp = int(price_text.replace("$", "").replace(" ", "").replace(".", ""))

        title = title_tag.get_text(strip=True)
        if title.endswith("..."):
            title = title_from_slug(title_tag["href"])

        products.append({
            "title": title,
            "url": title_tag["href"],
            "price_clp": price_clp,
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
