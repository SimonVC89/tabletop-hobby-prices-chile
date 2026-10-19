"""Conexion directa a Postgres (Supabase) y funciones de insercion.

No pasa por la Data API/PostgREST de Supabase a proposito: las tablas
quedaron sin exponer via API, y este scraper corre server-to-server
(igual que el backend via JDBC), asi que se conecta directo con la
connection string de Postgres.
"""

import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    database_url = os.environ["DATABASE_URL"]
    return psycopg2.connect(database_url)


def upsert_store(conn, name: str, base_url: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into stores (name, base_url)
            values (%s, %s)
            on conflict (name) do update set base_url = excluded.base_url
            returning id
            """,
            (name, base_url),
        )
        return cur.fetchone()[0]


def upsert_listing(conn, store_id: str, product: dict) -> str:
    # Un SKU vacio no choca con la restriccion UNIQUE (NULL <> NULL en
    # Postgres) y duplicaria el listing en cada corrida: mejor fallar.
    if not product.get("store_sku"):
        raise ValueError(f"Listing sin store_sku, no se puede guardar: {product.get('url')}")

    with conn.cursor() as cur:
        cur.execute(
            """
            insert into product_listings
                (store_id, raw_title, url, external_sku, image_url, description, last_seen_at)
            values (%s, %s, %s, %s, %s, %s, now())
            on conflict (store_id, external_sku) do update set
                raw_title = excluded.raw_title,
                url = excluded.url,
                image_url = excluded.image_url,
                description = excluded.description,
                last_seen_at = now(),
                is_active = true
            returning id
            """,
            (
                store_id,
                product["title"],
                product["url"],
                product["store_sku"],
                product.get("image_url"),
                product.get("description"),
            ),
        )
        return cur.fetchone()[0]


def insert_price_history(conn, listing_id: str, price_clp: int, in_stock: bool) -> bool:
    """Guarda el precio solo si cambio el precio o el stock respecto de la
    ultima fila del listing. Devuelve True si guardo una fila.

    price_history es un registro de CAMBIOS, no una foto por corrida: el
    precio vigente de un dia sin fila es el de la ultima fila anterior (mientras
    el listing siga apareciendo en la tienda, ver product_listings.last_seen_at).
    Asi se puede scrapear varias veces al dia sin que la tabla crezca: el 83% de
    las filas guardadas una vez por dia repetia el estado anterior.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into price_history (listing_id, price_clp, in_stock)
            select %(listing)s, %(price)s, %(stock)s
            where not exists (
                select 1 from (
                    select price_clp, in_stock from price_history
                    where listing_id = %(listing)s
                    order by scraped_at desc limit 1
                ) last
                where last.price_clp = %(price)s and last.in_stock = %(stock)s
            )
            """,
            {"listing": listing_id, "price": price_clp, "stock": in_stock},
        )
        return cur.rowcount == 1


def save_products(conn, store_id: str, products: list[dict]) -> tuple[int, int]:
    """Guarda los listings scrapeados de una tienda y los cambios de precio/stock.

    Devuelve (listings actualizados, filas nuevas en price_history). Es el bucle
    que antes se repetia en cada ingest_*.py.
    """
    changes = 0
    for product in products:
        listing_id = upsert_listing(conn, store_id, product)
        if insert_price_history(conn, listing_id, product["price_clp"], product["in_stock"]):
            changes += 1
    return len(products), changes
