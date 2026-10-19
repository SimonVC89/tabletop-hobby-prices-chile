"""Borra filas de price_history mas viejas que la retencion definida.

Borrado simple (no se comprime a un resumen antes de borrar) -- con el
margen de espacio actual en el free tier de Supabase no es urgente, se
puede revisar mas adelante si hace falta mas resolucion historica.

price_history guarda solo CAMBIOS (ver db.insert_price_history), asi que la
ultima fila anterior al corte de cada listing NO se borra aunque sea vieja:
es la que dice cual era el precio al inicio de la ventana y, si el precio no
cambio en meses, el precio vigente. Borrarla dejaria al listing sin precio.
"""

from src.db import get_connection

RETENTION_MONTHS = 8


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                delete from price_history ph
                where ph.scraped_at < now() - make_interval(months => %(months)s)
                  and exists (
                      select 1 from price_history newer
                      where newer.listing_id = ph.listing_id
                        and newer.scraped_at > ph.scraped_at
                        and newer.scraped_at < now() - make_interval(months => %(months)s)
                  )
                """,
                {"months": RETENTION_MONTHS},
            )
            print(f"Filas de price_history borradas: {cur.rowcount}")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
