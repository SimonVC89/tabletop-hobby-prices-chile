"""Borra filas de price_history mas viejas que la retencion definida.

Borrado simple (no se comprime a un resumen antes de borrar) -- con el
margen de espacio actual en el free tier de Supabase no es urgente, se
puede revisar mas adelante si hace falta mas resolucion historica.
"""

from src.db import get_connection

RETENTION_MONTHS = 8


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                delete from price_history
                where scraped_at < now() - make_interval(months => %s)
                """,
                (RETENTION_MONTHS,),
            )
            print(f"Filas de price_history borradas: {cur.rowcount}")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
