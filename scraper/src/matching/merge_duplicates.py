"""Fusiona los productos duplicados que se revisaron con find_duplicates.

    python -m src.matching.merge_duplicates                          # simulacion
    python -m src.matching.merge_duplicates --exclude A3,B7 --include B12
    python -m src.matching.merge_duplicates --apply                  # guarda

Toma los candidatos de duplicados_revision.json: se fusionan los que no
tenian alertas, menos los de --exclude, mas los de --include.

Por cada grupo, el producto con mas tiendas activas queda como principal:
- los listings de los demas pasan a el (el historial de precios vive en cada
  listing, asi que viaja con ellos);
- la clave de matching de cada absorbido queda como alias del principal,
  para que assign_products una ahi los listings nuevos con esa clave;
- los absorbidos no se borran: quedan ocultos y con merged_into apuntando al
  principal. Sus listings conservan su match_key, asi que se puede deshacer.

Sin --apply todo corre en una transaccion que se revierte al final: los
numeros que muestra son los reales, pero no se guarda nada.
"""

import argparse
import json

from src.db import get_connection
from src.matching.find_duplicates import DECISIONS_PATH


def parse_ids(value: str) -> set[str]:
    return {v.strip().upper() for v in value.split(",") if v.strip()}


def chosen_candidates(decisions, exclude: set[str], include: set[str]):
    known = {d["id"] for d in decisions}
    unknown = (exclude | include) - known
    if unknown:
        raise SystemExit(f"Ids que no estan en el informe: {', '.join(sorted(unknown))}")
    return [d for d in decisions if (d["merge_by_default"] and d["id"] not in exclude) or d["id"] in include]


def resolve(cur, product_id: str) -> str:
    """Sigue merged_into hasta el producto vigente. Los pares encadenados
    (X=Y y despues Y=Z) se convierten asi en X=Z en vez de perder a Z."""
    seen = set()
    while product_id not in seen:
        seen.add(product_id)
        cur.execute("select merged_into::text from products where id = %s", (product_id,))
        row = cur.fetchone()
        if not row or row[0] is None:
            return product_id
        product_id = row[0]
    return product_id


def merge_group(cur, product_ids: list[str]):
    """Fusiona un grupo. Devuelve (principal, absorbidos, listings movidos) o None si no queda nada que fusionar."""
    product_ids = sorted({resolve(cur, pid) for pid in product_ids})
    cur.execute(
        """
        select p.id::text, p.canonical_name, p.match_key, p.image_url, p.description,
               count(distinct pl.store_id) filter (where pl.is_active) as stores,
               count(pl.id) as listings
        from products p
        left join product_listings pl on pl.product_id = p.id
        where p.id::text = any(%s) and p.merged_into is null
        group by p.id
        """,
        (product_ids,),
    )
    rows = [dict(zip(("id", "name", "match_key", "image_url", "description", "stores", "listings"), r))
            for r in cur.fetchall()]
    # Si la base cambio desde la revision (o se corrio dos veces), puede que
    # ya no queden dos productos sin fusionar en el grupo.
    if len(rows) < 2:
        return None

    survivor = max(rows, key=lambda r: (r["stores"], r["listings"], r["image_url"] is not None))
    absorbed = [r for r in rows if r["id"] != survivor["id"]]
    moved = 0

    for r in absorbed:
        cur.execute("update product_listings set product_id = %s where product_id = %s", (survivor["id"], r["id"]))
        moved += cur.rowcount
        if r["match_key"] and r["match_key"] != survivor["match_key"]:
            cur.execute(
                """
                insert into product_aliases (match_key, product_id) values (%s, %s)
                on conflict (match_key) do update set product_id = excluded.product_id
                """,
                (r["match_key"], survivor["id"]),
            )
        # Alias que apuntaban al absorbido (de una fusion anterior) pasan al principal.
        cur.execute("update product_aliases set product_id = %s where product_id = %s", (survivor["id"], r["id"]))
        cur.execute(
            "update products set merged_into = %s, hidden_at = coalesce(hidden_at, now()) where id = %s",
            (survivor["id"], r["id"]),
        )

    # Si el principal no tenia imagen o descripcion, hereda la de un absorbido.
    for field in ("image_url", "description"):
        if not survivor[field]:
            donor = next((r[field] for r in absorbed if r[field]), None)
            if donor:
                cur.execute(f"update products set {field} = %s where id = %s", (donor, survivor["id"]))

    return survivor, absorbed, moved


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--exclude", type=parse_ids, default=set(), help="ids sin alerta que NO se fusionan")
    parser.add_argument("--include", type=parse_ids, default=set(), help="ids con alerta que SI se fusionan")
    parser.add_argument("--apply", action="store_true", help="guardar los cambios (sin esto, solo simula)")
    args = parser.parse_args()

    if not DECISIONS_PATH.exists():
        raise SystemExit(f"No existe {DECISIONS_PATH.name}: corre primero python -m src.matching.find_duplicates")
    decisions = json.loads(DECISIONS_PATH.read_text(encoding="utf-8"))
    chosen = chosen_candidates(decisions, args.exclude, args.include)

    conn = get_connection()
    merged_groups = absorbed_total = moved_total = 0
    try:
        with conn.cursor() as cur:
            for candidate in chosen:
                result = merge_group(cur, [p["id"] for p in candidate["products"]])
                if result is None:
                    print(f"  {candidate['id']}: ya fusionado o sin productos vigentes, se omite")
                    continue
                survivor, absorbed, moved = result
                merged_groups += 1
                absorbed_total += len(absorbed)
                moved_total += moved
                print(f"  {candidate['id']}: {survivor['name']} <- {', '.join(r['name'] for r in absorbed)}")

        if args.apply:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()

    mode = "GUARDADO" if args.apply else "SIMULACION (no se guardo nada; usa --apply)"
    print(f"\n{mode}: {merged_groups} grupos, {absorbed_total} productos absorbidos, {moved_total} listings movidos")
    if args.apply:
        print("Siguiente: display_names, classify y refresh_price_views para recalcular nombres y precios.")


if __name__ == "__main__":
    main()
