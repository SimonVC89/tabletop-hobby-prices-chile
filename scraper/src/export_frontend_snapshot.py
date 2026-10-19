"""Exporta un snapshot real de la base a JSON para desarrollar el frontend.

Mientras no exista el backend, el frontend consume estos archivos desde
frontend/public/mock/ a traves de una capa api/ con el mismo contrato que
tendran los endpoints REST (ver frontend/src/api/types.ts). Los archivos
generados no se versionan: se regeneran corriendo este script.

    python -m src.export_frontend_snapshot
"""

import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from pgvector.psycopg2 import register_vector

from src.db import get_connection
from src.manual_stores import MANUAL_ONLY_STORES
from src.matching.normalize import strip_accents

OUT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "public" / "mock"
MIN_STORES_FOR_MEDIAN = 3
OFFER_THRESHOLD = 20
DESTACADA_THRESHOLD = 50
SIMILAR_COUNT = 6
# Primer dia (hora de Chile) en que price_history guarda solo cambios, no una
# fila por scraping. Ver db.insert_price_history y export_details.
CHANGES_ONLY_FROM = date(2026, 10, 19)

# "Relacionados": los embeddings se calculan sobre el TITULO, asi que captan
# sagas y nombres parecidos, no mecanicas (a Azul le salian "Bluey" y "Pokebola
# Tin Azul"). Bajo ~0.78 todo es ruido, asi que solo entran:
#  - juegos de la misma saga (misma primera palabra del nombre) con un minimo
#    de similitud, para descartar homonimos ("Star Realms" vs "Star Trek");
#  - juegos con titulo casi identico por embeddings.
# Y solo los que hoy se pueden comprar.
# 0.45: las ediciones con licencia ("Dobble Paw Patrol" / "Dobble Spiderman")
# comparten saga pero el tema domina el titulo y la similitud queda en ~0.5.
FAMILY_MIN_SCORE = 0.45
SIMILAR_MIN_SCORE = 0.78
FAMILY_BONUS = 0.15  # la saga va antes que un parecido por embedding
FAMILY_STOPWORDS = {"el", "la", "los", "las", "un", "una", "the", "de", "del"}
# Primeras palabras que no identifican una saga ("Juego de ...", "Pack ...").
GENERIC_FIRST_WORDS = {
    "juego", "juegos", "pack", "kit", "set", "caja", "mini", "super", "gran", "expansion",
    "ampliacion", "cartas", "tablero", "mazo", "tapete", "dados", "libro", "guia",
}


# Palabras iniciales compartidas por sagas que no tienen nada que ver ("Star
# Realms" / "Star Wars" / "Star Trek"): para estas la saga se identifica con
# las dos primeras palabras.
AMBIGUOUS_FIRST_WORDS = {
    "star", "dark", "black", "blue", "red", "white", "gold", "golden", "love", "happy", "little", "big", "mega",
}


def family_key(name: str) -> str | None:
    """Identifica la saga de un juego por el inicio de su nombre ("Catan Junior" -> "catan")."""
    words = re.sub(r"[^a-z0-9]+", " ", strip_accents(name).lower()).split()
    while words and words[0] in FAMILY_STOPWORDS:
        words.pop(0)
    if not words or words[0] in GENERIC_FIRST_WORDS:
        return None
    if len(words[0]) >= 4 and words[0] not in AMBIGUOUS_FIRST_WORDS:
        return words[0]
    # Palabra inicial corta ("7 Wonders", "Ark Nova"): se necesitan dos.
    return " ".join(words[:2]) if len(words) >= 2 else None


def rows(cur, sql, params=()):
    cur.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def discount(best, median, store_count):
    if best is None or median is None or store_count < MIN_STORES_FOR_MEDIAN or best >= median:
        return None
    return round(100 * (median - best) / median, 1)


def export_stores(cur):
    data = rows(cur, """
        select s.id::text, s.name, s.base_url, s.active,
               count(pl.id) filter (where pl.is_active) as active_listings
        from stores s left join product_listings pl on pl.store_id = s.id
        group by s.id order by s.name
    """)

    def status(store):
        if not store["active"]:
            return "excluded"
        return "manual" if store["name"] in MANUAL_ONLY_STORES else "daily"

    return [
        {
            "id": s["id"],
            "name": s["name"],
            "baseUrl": s["base_url"],
            "activeListings": s["active_listings"],
            "status": status(s),
        }
        for s in data
    ]


def export_products(cur):
    # Todos los juegos visibles, tambien los agotados en todas las tiendas:
    # de esos se informa el ultimo precio visto y cuando.
    data = rows(cur, """
        with best as (
            select distinct on (cp.product_id)
                   cp.product_id, cp.price_clp, s.name as store_name
            from current_prices cp join stores s on s.id = cp.store_id
            where cp.in_stock
            order by cp.product_id, cp.price_clp
        ),
        -- price_history guarda solo cambios: la fecha en que "se vio" el precio es
        -- la ultima vez que la tienda mostro el listing, no la de la fila.
        last_seen as (
            select distinct on (pl.product_id)
                   pl.product_id, ph.price_clp, pl.last_seen_at as scraped_at
            from product_listings pl
            join lateral (
                select price_clp from price_history
                where listing_id = pl.id order by scraped_at desc limit 1
            ) ph on true
            order by pl.product_id, pl.last_seen_at desc, ph.price_clp
        )
        select p.id::text, p.canonical_name, p.image_url,
               coalesce(pps.store_count, 0) as store_count,
               b.price_clp as best_price, b.store_name as best_store,
               round(pps.median_price_clp)::int as median_price,
               ls.price_clp as last_price, ls.scraped_at as last_seen_at
        from products p
        left join best b on b.product_id = p.id
        left join last_seen ls on ls.product_id = p.id
        left join product_price_stats pps on pps.product_id = p.id
        where p.hidden_at is null and p.category = 'board_game'
    """)
    return [
        {
            "id": p["id"],
            "name": p["canonical_name"],
            "imageUrl": p["image_url"],
            "storeCount": p["store_count"],
            "bestPrice": p["best_price"],
            "bestStoreName": p["best_store"],
            "medianPrice": p["median_price"],
            "discountPct": discount(p["best_price"], p["median_price"], p["store_count"]),
            "lastPrice": p["last_price"] if p["best_price"] is None else None,
            "lastSeenAt": p["last_seen_at"].isoformat() if p["best_price"] is None and p["last_seen_at"] else None,
        }
        for p in data
    ]


def export_offers(cur):
    # Una oferta por tienda y juego: si la tienda lo publica en dos paginas,
    # se queda la mas barata.
    data = rows(cur, """
        select distinct on (cp.product_id, cp.store_id)
               p.id::text as product_id, p.canonical_name, p.image_url,
               s.name as store_name, pl.url, cp.price_clp,
               round(pps.median_price_clp)::int as median_price, pps.store_count,
               pps.min_price_clp, pps.max_price_clp
        from current_prices cp
        join product_price_stats pps on pps.product_id = cp.product_id
        join products p on p.id = cp.product_id
        join stores s on s.id = cp.store_id
        join product_listings pl on pl.id = cp.listing_id
        where pps.store_count >= %s and cp.in_stock
          and cp.price_clp < pps.median_price_clp
          and p.hidden_at is null and p.category = 'board_game'
        order by cp.product_id, cp.store_id, cp.price_clp
    """, (MIN_STORES_FOR_MEDIAN,))

    offers = []
    for o in data:
        pct = discount(o["price_clp"], o["median_price"], o["store_count"])
        if pct is None or pct < OFFER_THRESHOLD:
            continue
        offers.append({
            "productId": o["product_id"],
            "productName": o["canonical_name"],
            "imageUrl": o["image_url"],
            "storeName": o["store_name"],
            "listingUrl": o["url"],
            "price": o["price_clp"],
            "medianPrice": o["median_price"],
            "minPrice": o["min_price_clp"],
            "maxPrice": o["max_price_clp"],
            "discountPct": pct,
            "storeCount": o["store_count"],
            "tier": "destacada" if pct >= DESTACADA_THRESHOLD else "oferta",
        })
    offers.sort(key=lambda o: -o["discountPct"])
    return offers


def export_details(cur, product_ids):
    products = {p["id"]: p for p in rows(cur, """
        select p.id::text, p.canonical_name, p.image_url, p.description, p.description_source,
               round(pps.median_price_clp)::int as median_price,
               pps.min_price_clp, pps.max_price_clp, pps.store_count
        from products p left join product_price_stats pps on pps.product_id = p.id
        where p.id::text = any(%s)
    """, (product_ids,))}

    # Un listing por tienda: el activo mas barato con stock, igual que la
    # mediana (algunas tiendas publican el mismo juego en dos paginas). Si la
    # tienda ya no lo publica, su ultimo precio visto, marcado sin stock. Las
    # tiendas excluidas no se listan (su link lleva a un sitio que no seguimos).
    listings = defaultdict(list)
    for l in rows(cur, """
        with latest as (
            select distinct on (ph.listing_id) ph.listing_id, ph.price_clp, ph.in_stock
            from price_history ph join product_listings pl on pl.id = ph.listing_id
            where pl.product_id::text = any(%s)
            order by ph.listing_id, ph.scraped_at desc
        )
        select distinct on (pl.product_id, pl.store_id)
               pl.product_id::text, s.id::text as store_id, s.name as store_name,
               pl.url, l.price_clp, (l.in_stock and pl.is_active) as in_stock, pl.last_seen_at
        from product_listings pl
        join latest l on l.listing_id = pl.id
        join stores s on s.id = pl.store_id
        where pl.product_id::text = any(%s) and s.active
        order by pl.product_id, pl.store_id, pl.is_active desc,
                 (l.in_stock and pl.is_active) desc, l.price_clp
    """, (product_ids, product_ids)):
        listings[l["product_id"]].append({
            "storeId": l["store_id"],
            "storeName": l["store_name"],
            "url": l["url"],
            "price": l["price_clp"],
            "inStock": l["in_stock"],
            "lastSeenAt": l["last_seen_at"].isoformat(),
        })

    # Un punto por tienda y dia: el precio mas bajo con stock de ese dia (si la
    # tienda tiene el juego en dos paginas, cuenta la mas barata).
    #
    # price_history guarda solo cambios, asi que cada dia se reconstruye: el
    # estado de un listing vale desde su fila hasta el dia anterior a la
    # siguiente, y la ultima fila vale hasta la ultima vez que la tienda mostro
    # el listing (o hasta el ultimo scraping si sigue activo). Los dias son de
    # Chile, no UTC: una corrida de las 23:10 hora de Chile es de ese dia.
    cur.execute("select (max(last_seen_at) at time zone 'America/Santiago')::date from product_listings")
    last_scrape_day = cur.fetchone()[0]

    listing_days = defaultdict(dict)  # listing_id -> {dia: (precio, en_stock)}; manda la ultima fila del dia
    listing_info = {}
    for h in rows(cur, """
        select pl.id::text as listing_id, pl.product_id::text, s.id::text as store_id, s.name as store_name,
               pl.is_active, (pl.last_seen_at at time zone 'America/Santiago')::date as seen_day,
               (ph.scraped_at at time zone 'America/Santiago')::date as day, ph.price_clp, ph.in_stock
        from price_history ph
        join product_listings pl on pl.id = ph.listing_id
        join stores s on s.id = pl.store_id
        where pl.product_id::text = any(%s)
        order by pl.id, ph.scraped_at
    """, (product_ids,)):
        listing_days[h["listing_id"]][h["day"]] = (h["price_clp"], h["in_stock"])
        listing_info[h["listing_id"]] = h

    # Antes de CHANGES_ONLY_FROM se guardaba una fila por listing en cada
    # scraping, asi que un dia sin fila es un dia SIN scraping (desconocido, no
    # "sin cambios"): ahi no se rellena y el grafico muestra el hueco. Desde esa
    # fecha, un dia sin fila es un precio que no cambio.
    scraped_days = defaultdict(set)  # tienda -> dias con scraping anteriores al registro de cambios
    for listing_id, days in listing_days.items():
        scraped_days[listing_info[listing_id]["store_id"]] |= {d for d in days if d < CHANGES_ONLY_FROM}

    history = defaultdict(lambda: defaultdict(dict))  # producto -> tienda -> dia(iso) -> (precio, en_stock)
    store_names = {}
    for listing_id, days in listing_days.items():
        info = listing_info[listing_id]
        store_names[info["store_id"]] = info["store_name"]
        end = last_scrape_day if info["is_active"] else info["seen_day"]
        known = scraped_days[info["store_id"]]
        by_day = history[info["product_id"]][info["store_id"]]
        ordered = sorted(days.items())
        for i, (day, (price, in_stock)) in enumerate(ordered):
            stop = ordered[i + 1][0] - timedelta(days=1) if i + 1 < len(ordered) else end
            for offset in range(max((stop - day).days, 0) + 1):
                d = day + timedelta(days=offset)
                if offset and d < CHANGES_ONLY_FROM and d not in known:
                    continue
                key = d.isoformat()
                # Entre listings de una misma tienda: con stock primero, y el mas barato.
                if key not in by_day or (not in_stock, price) < (not by_day[key][1], by_day[key][0]):
                    by_day[key] = (price, in_stock)

    details = {}
    for pid in product_ids:
        p = products.get(pid)
        if not p:
            continue
        stats = None
        if p["median_price"] is not None:
            stats = {
                "medianPrice": p["median_price"],
                "minPrice": p["min_price_clp"],
                "maxPrice": p["max_price_clp"],
                "storeCount": p["store_count"],
            }
        series = [
            {
                "storeId": sid,
                "storeName": store_names[sid],
                "points": [
                    {"date": d, "price": price, "inStock": in_stock}
                    for d, (price, in_stock) in sorted(days.items())
                ],
            }
            for sid, days in history[pid].items()
        ]
        series.sort(key=lambda s: s["storeName"])
        details[pid] = {
            "detail": {
                "id": pid,
                "name": p["canonical_name"],
                "imageUrl": p["image_url"],
                "description": p["description"],
                "descriptionSource": p["description_source"] if p["description"] else None,
                "listings": sorted(listings[pid], key=lambda l: l["price"]),
                "stats": stats,
            },
            "history": {"productId": pid, "series": series},
        }
    return details


def compute_similar(cur, target_ids, summaries_by_id):
    """Juegos relacionados: de la misma saga o con titulo casi identico, solo con stock.

    Usa el embedding promedio de los listings de cada producto (ver las
    constantes FAMILY_* / SIMILAR_* arriba para el porque de los umbrales).
    """
    vectors = defaultdict(list)
    cur.execute("""
        select product_id::text, title_embedding from product_listings
        where product_id is not null and title_embedding is not null
    """)
    for pid, emb in cur.fetchall():
        if pid in summaries_by_id:
            vectors[pid].append(emb)

    ids = list(vectors)
    matrix = np.array([np.mean(vectors[i], axis=0) for i in ids], dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
    index_of = {pid: i for i, pid in enumerate(ids)}
    families = [family_key(summaries_by_id[pid]["name"]) for pid in ids]
    # Solo se sugieren juegos que hoy se pueden comprar (aunque el actual no).
    buyable = np.array([summaries_by_id[pid]["bestPrice"] is not None for pid in ids])

    similar = {}
    for pid in target_ids:
        if pid not in index_of:
            continue
        me = index_of[pid]
        scores = matrix @ matrix[me]
        same_family = np.array([families[me] is not None and f == families[me] for f in families])

        eligible = buyable & (scores >= SIMILAR_MIN_SCORE) | buyable & same_family & (scores >= FAMILY_MIN_SCORE)
        eligible[me] = False
        ranking = np.where(eligible, scores + FAMILY_BONUS * same_family, -np.inf)
        top = [i for i in np.argsort(-ranking)[:SIMILAR_COUNT] if np.isfinite(ranking[i])]
        similar[pid] = [summaries_by_id[ids[i]] for i in top]
    return similar


def write(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    conn = get_connection()
    register_vector(conn)
    try:
        with conn.cursor() as cur:
            # Ultimo scraping, no la ultima fila de price_history (que ahora solo guarda cambios).
            cur.execute("select max(last_seen_at) from product_listings")
            meta = {"lastUpdated": cur.fetchone()[0].isoformat()}
            stores = export_stores(cur)
            products = export_products(cur)
            offers = export_offers(cur)

            summaries_by_id = {p["id"]: p for p in products}
            detail_ids = sorted(summaries_by_id)
            details = export_details(cur, detail_ids)
            similar = compute_similar(cur, detail_ids, summaries_by_id)
    finally:
        conn.close()

    write(OUT_DIR / "meta.json", meta)
    write(OUT_DIR / "stores.json", stores)
    write(OUT_DIR / "products.json", products)
    write(OUT_DIR / "offers.json", offers)
    # Fichas de productos que ya no existen (fusionados u ocultos) no deben sobrevivir.
    for stale in (OUT_DIR / "products").glob("*.json"):
        stale.unlink()
    for pid, d in details.items():
        write(OUT_DIR / "products" / f"{pid}.json", {**d, "similar": similar.get(pid, [])})

    in_stock = sum(1 for p in products if p["bestPrice"] is not None)
    print(f"Tiendas: {len(stores)} | Productos: {len(products)} ({in_stock} con stock) | "
          f"Ofertas: {len(offers)} | Fichas con detalle: {len(details)}")
    print(f"Salida: {OUT_DIR}")


if __name__ == "__main__":
    main()
