"""Calcula match_key de los listings.

    python -m src.matching.compute_keys          # solo los que no tienen
    python -m src.matching.compute_keys --all    # recalcula todos

--all se usa cuando cambian las reglas de normalizacion: los listings cuya
clave cambio se desvinculan de su producto (product_id = NULL) para que
assign_products los reagrupe con la clave nueva. El historial de precios
no se toca: vive en cada listing.
"""

import sys

from src.db import get_connection
from src.matching.normalize import build_match_key


def main():
    recompute_all = "--all" in sys.argv
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            where = "" if recompute_all else "where match_key is null"
            cur.execute(f"select id, raw_title, match_key from product_listings {where}")
            rows = cur.fetchall()

        changed = 0
        with conn.cursor() as cur:
            for listing_id, raw_title, old_key in rows:
                key = build_match_key(raw_title)
                if key == old_key:
                    continue
                changed += 1
                if old_key is None:
                    cur.execute(
                        "update product_listings set match_key = %s where id = %s",
                        (key, listing_id),
                    )
                else:
                    cur.execute(
                        "update product_listings set match_key = %s, product_id = null where id = %s",
                        (key, listing_id),
                    )

        conn.commit()
        print(f"Listings revisados: {len(rows)} | claves nuevas o cambiadas: {changed}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
