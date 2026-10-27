"""Corre el scraper de Café 2d6 y persiste los resultados en Supabase."""

from src.ingest import run_ingest
from src.scrapers.cafe2d6 import CATEGORY_URL, fetch_all_products

STORE_NAME = "Café 2d6"
STORE_BASE_URL = "https://www.cafe2d6.cl"


def main():
    run_ingest(STORE_NAME, STORE_BASE_URL, lambda: fetch_all_products(CATEGORY_URL))


if __name__ == "__main__":
    main()
