"""Crea/vincula products a partir del match_key de cada listing.

Por cada match_key distinto entre los listings sin product_id:
- si ya existe un product con ese match_key, se vinculan los listings a el
- si no existe, se crea un product nuevo (canonical_name = el raw_title
  mas largo del grupo, asumiendo que suele ser el mas descriptivo) y se
  vinculan los listings

Solo trabaja sobre category='board_game' por ahora.
"""

from src.db import get_connection

CATEGORY = "board_game"


def get_or_create_product(conn, match_key: str, listings: list[tuple]) -> str:
    with conn.cursor() as cur:
        cur.execute(
            "select id from products where match_key = %s and category = %s",
            (match_key, CATEGORY),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        # mismo listing (el de titulo mas largo/descriptivo) aporta el
        # nombre canonico y tambien su imagen/descripcion
        _, best_title, best_image_url, best_description = max(listings, key=lambda l: len(l[1]))
        cur.execute(
            """
            insert into products (category, canonical_name, match_key, image_url, description)
            values (%s, %s, %s, %s, %s)
            returning id
            """,
            (CATEGORY, best_title, match_key, best_image_url, best_description),
        )
        return cur.fetchone()[0]


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "select id, match_key, raw_title, image_url, description "
                "from product_listings where product_id is null"
            )
            rows = cur.fetchall()

        print(f"Listings sin product_id: {len(rows)}")

        groups: dict[str, list[tuple]] = {}
        for listing_id, match_key, raw_title, image_url, description in rows:
            groups.setdefault(match_key, []).append((listing_id, raw_title, image_url, description))

        print(f"Grupos (match_key) distintos: {len(groups)}")

        with conn.cursor() as cur:
            for match_key, listings in groups.items():
                product_id = get_or_create_product(conn, match_key, listings)

                for listing_id, *_ in listings:
                    cur.execute(
                        "update product_listings set product_id = %s where id = %s",
                        (product_id, listing_id),
                    )

        conn.commit()
        print("Listo.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
