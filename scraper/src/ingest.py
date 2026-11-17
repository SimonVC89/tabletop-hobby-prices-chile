"""Lo comun a cada src.ingest_*: scrapear una tienda y guardar sus listings en Supabase.

Dos casos que no son "todo bien" aunque el scraper no lance error:
- La tienda esta cerrada al publico (StoreClosedError): se avisa con una advertencia
  y no se guarda nada. No es una falla: sus listings pasan a inactivos a los
  STALE_AFTER_DAYS y se reactivan solos cuando la tienda vuelve a abrir.
- La tienda esta abierta pero el scraper no encontro ningun producto: o cambio su
  HTML, o a la IP del runner le llego una pagina de bloqueo o verificacion (le pasa
  a veces a Griffin Games y Diverti en la misma corrida). Es una falla (sale con
  error), para que entre en la regla de src/retry_failed_stores.py en vez de pasar
  en silencio. El mensaje dice que pagina llego, para distinguir un caso del otro.
"""

from collections.abc import Callable

from src.db import get_connection, save_products, upsert_store
from src.http import StoreClosedError, last_page


class NoProductsError(Exception):
    """La tienda respondio, pero el scraper no encontro ningun producto."""


def scrape(store_name: str, fetch_products: Callable[[], list[dict]]) -> list[dict] | None:
    """Los productos de la tienda, o None si esta cerrada al publico."""
    try:
        products = fetch_products()
    except StoreClosedError as e:
        # Anotacion visible en el resumen de la corrida en GitHub.
        print(f"::warning::{store_name} esta cerrada al publico ({e}); no se actualiza. "
              "Sus listings vuelven solos cuando la tienda abra de nuevo.")
        return None
    if not products:
        page = last_page()
        received = page.describe() if page else "sin datos de la pagina"
        # Tambien como anotacion: queda en el resumen de la corrida y se lee por la API.
        print(f"::warning::{store_name}: 0 productos. Llego: {received}")
        raise NoProductsError(f"{store_name}: 0 productos. La tienda respondio pero el scraper no "
                              f"encontro nada (cambio su HTML o una pagina de bloqueo). Llego: {received}")
    return products


def run_ingest(store_name: str, base_url: str, fetch_products: Callable[[], list[dict]]) -> None:
    products = scrape(store_name, fetch_products)
    if products is None:
        return
    print(f"Scrapeados {len(products)} productos. Guardando en Supabase...")

    conn = get_connection()
    try:
        store_id = upsert_store(conn, store_name, base_url)

        listings, changes = save_products(conn, store_id, products)

        conn.commit()
        print(f"Listo: {listings} listings actualizados, {changes} cambios de precio o stock guardados en price_history.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
