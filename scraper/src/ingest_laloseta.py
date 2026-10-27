"""Corre el scraper de La Loseta y persiste los resultados en Supabase."""

from src.ingest import run_ingest
from src.scrapers.laloseta import CATEGORY_URL, fetch_all_products

STORE_NAME = "La Loseta"
STORE_BASE_URL = "https://laloseta.cl"


def main():
    run_ingest(STORE_NAME, STORE_BASE_URL, lambda: fetch_all_products(CATEGORY_URL))


if __name__ == "__main__":
    main()
