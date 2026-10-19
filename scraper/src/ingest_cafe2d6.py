"""Corre el scraper de Café 2d6 y persiste los resultados en Supabase."""

from src.db import get_connection, save_products, upsert_store
from src.scrapers.cafe2d6 import CATEGORY_URL, fetch_all_products

STORE_NAME = "Café 2d6"
STORE_BASE_URL = "https://www.cafe2d6.cl"


def main():
    products = fetch_all_products(CATEGORY_URL)
    print(f"Scrapeados {len(products)} productos. Guardando en Supabase...")

    conn = get_connection()
    try:
        store_id = upsert_store(conn, STORE_NAME, STORE_BASE_URL)

        listings, changes = save_products(conn, store_id, products)

        conn.commit()
        print(f"Listo: {listings} listings actualizados, {changes} cambios de precio o stock guardados en price_history.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
