"""Corre el scraper de DeMente Games y persiste los resultados en Supabase."""

from src.ingest import run_ingest
from src.scrapers.dementegames import CATEGORY_URL, fetch_all_products

STORE_NAME = "DeMente Games"
STORE_BASE_URL = "https://dementegames.cl"


def main():
    run_ingest(STORE_NAME, STORE_BASE_URL, lambda: fetch_all_products(CATEGORY_URL))


if __name__ == "__main__":
    main()
