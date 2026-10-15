"""Oculta productos sin ningun listing activo hace 6+ meses (soft-delete).

No se borra nada: hidden_at se usa para que el frontend/API dejen de
mostrarlo en busquedas normales. Si vuelve a aparecer en alguna tienda,
se reactiva solo.
"""

from src.db import get_connection

DISCONTINUED_AFTER_MONTHS = 6


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                update products p
                set hidden_at = now()
                where hidden_at is null
                  and not exists (
                      select 1 from product_listings pl
                      where pl.product_id = p.id and pl.is_active
                  )
                  and not exists (
                      select 1 from product_listings pl
                      where pl.product_id = p.id
                        and pl.last_seen_at > now() - make_interval(months => %s)
                  )
                """,
                (DISCONTINUED_AFTER_MONTHS,),
            )
            print(f"Productos ocultados por descontinuados: {cur.rowcount}")

            cur.execute(
                """
                update products p
                set hidden_at = null
                where hidden_at is not null
                  and exists (
                      select 1 from product_listings pl
                      where pl.product_id = p.id and pl.is_active
                  )
                """
            )
            print(f"Productos reactivados (volvieron a verse en alguna tienda): {cur.rowcount}")

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
