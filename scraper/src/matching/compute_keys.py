"""Calcula match_key para los listings que todavia no lo tienen."""

from src.db import get_connection
from src.matching.normalize import build_match_key


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("select id, raw_title from product_listings where match_key is null")
            rows = cur.fetchall()

        print(f"Listings sin match_key: {len(rows)}")

        with conn.cursor() as cur:
            for listing_id, raw_title in rows:
                key = build_match_key(raw_title)
                cur.execute(
                    "update product_listings set match_key = %s where id = %s",
                    (key, listing_id),
                )

        conn.commit()
        print("Listo.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
