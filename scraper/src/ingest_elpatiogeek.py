"""Corre el scraper de El Patio Geek y persiste los resultados en Supabase."""

from src.ingest import run_ingest
from src.scrapers.elpatiogeek import CATEGORY_URL, fetch_all_products

STORE_NAME = "El Patio Geek"
STORE_BASE_URL = "https://www.elpatiogeek.cl"


def main():
    run_ingest(STORE_NAME, STORE_BASE_URL, lambda: fetch_all_products(CATEGORY_URL))


if __name__ == "__main__":
    main()
