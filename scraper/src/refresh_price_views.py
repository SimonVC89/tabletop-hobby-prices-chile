"""Refresca las vistas materializadas de precio despues de cada scrape."""

from src.db import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("refresh materialized view current_prices")
            cur.execute("refresh materialized view product_price_stats")
        conn.commit()
        print("Vistas materializadas refrescadas.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
