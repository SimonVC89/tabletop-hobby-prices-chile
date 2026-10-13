"""Corre el scraper de Cafe 2d6 y persiste los resultados en Supabase."""

from src.db import get_connection, insert_price_history, upsert_listing, upsert_store
from src.scrapers.cafe2d6 import CATEGORY_URL, fetch_all_products

STORE_NAME = "Cafe 2d6"
STORE_BASE_URL = "https://www.cafe2d6.cl"


def main():
    products = fetch_all_products(CATEGORY_URL)
    print(f"Scrapeados {len(products)} productos. Guardando en Supabase...")

    conn = get_connection()
    try:
        store_id = upsert_store(conn, STORE_NAME, STORE_BASE_URL)

        for product in products:
            listing_id = upsert_listing(conn, store_id, product)
            insert_price_history(conn, listing_id, product["price_clp"], product["in_stock"])

        conn.commit()
        print(f"Listo: {len(products)} listings actualizados, {len(products)} filas nuevas en price_history.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
