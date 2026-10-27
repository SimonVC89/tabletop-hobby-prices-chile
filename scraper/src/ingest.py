"""Lo comun a cada src.ingest_*: scrapear una tienda y guardar sus listings en Supabase.

Dos casos que no son "todo bien" aunque el scraper no lance error:
- La tienda esta cerrada al publico (StoreClosedError): se avisa con una advertencia
  y no se guarda nada. No es una falla: sus listings pasan a inactivos a los
  STALE_AFTER_DAYS y se reactivan solos cuando la tienda vuelve a abrir.
- La tienda esta abierta pero el scraper no encontro ningun producto: casi seguro
  cambio su HTML. Es una falla (sale con error), para que entre en la regla de
  src/retry_failed_stores.py en vez de pasar en silencio.
"""

from collections.abc import Callable

from src.db import get_connection, save_products, upsert_store
from src.http import StoreClosedError


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
        raise NoProductsError(f"{store_name}: 0 productos. La tienda respondio pero el scraper no "
                              "encontro nada; probablemente cambio su HTML.")
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
