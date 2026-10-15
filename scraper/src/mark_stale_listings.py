"""Marca is_active=false en listings que no se vieron en el scraping reciente.

Se corre despues de todos los steps de scraping del dia. El margen de 3
dias (en vez de 1) tolera que una tienda falle una corrida puntual sin
que eso se interprete como "desaparecio" de inmediato.
"""

from src.db import get_connection

STALE_AFTER_DAYS = 3


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                update product_listings
                set is_active = false
                where is_active
                  and last_seen_at < now() - make_interval(days => %s)
                """,
                (STALE_AFTER_DAYS,),
            )
            print(f"Listings marcados como inactivos: {cur.rowcount}")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
