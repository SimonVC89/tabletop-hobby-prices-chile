"""Corre el scraper de Griffin Games y persiste los resultados en Supabase."""

from src.ingest import run_ingest
from src.scrapers.griffingames import CATEGORY_URL, fetch_all_products

STORE_NAME = "Griffin Games"
STORE_BASE_URL = "https://www.griffingames.cl"


def main():
    run_ingest(STORE_NAME, STORE_BASE_URL, lambda: fetch_all_products(CATEGORY_URL))


if __name__ == "__main__":
    main()
