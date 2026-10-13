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
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into product_listings (store_id, raw_title, url, external_sku, last_seen_at)
            values (%s, %s, %s, %s, now())
            on conflict (store_id, external_sku) do update set
                raw_title = excluded.raw_title,
                url = excluded.url,
                last_seen_at = now(),
                is_active = true
            returning id
            """,
            (store_id, product["title"], product["url"], product["store_sku"]),
        )
        return cur.fetchone()[0]


def insert_price_history(conn, listing_id: str, price_clp: int, in_stock: bool):
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into price_history (listing_id, price_clp, in_stock)
            values (%s, %s, %s)
            """,
            (listing_id, price_clp, in_stock),
        )
