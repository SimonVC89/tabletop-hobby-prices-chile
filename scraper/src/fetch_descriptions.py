"""Completa la descripcion corta de los productos que no la tienen.

    python -m src.fetch_descriptions --dry-run --limit 60     # prueba: no guarda nada
    python -m src.fetch_descriptions                          # una pasada sin tope
    python -m src.fetch_descriptions --limit 150 --skip-stores UpDown   # asi corre el cron
    python -m src.fetch_descriptions --revalidate             # reaplica las reglas a lo ya guardado

Los scrapers diarios leen la grilla del catalogo, que solo trae el titulo
repetido; el texto real esta en la pagina de cada producto. Por cada producto
sin descripcion util:

1. Sin pedidos: si algun listing ya trae una descripcion util, se adopta.
2. Con pedidos: se pide la pagina de UN listing por producto, de la tienda
   con mejores descripciones que lo venda y que no se haya revisado antes. Si
   no sirvio, la siguiente corrida prueba con la siguiente tienda.

Cuidados con las tiendas: se respeta su robots.txt, hay como maximo un pedido
cada DELAY_SECONDS por tienda (las tiendas corren en paralelo entre si) y el
avance se guarda en la base: se puede cortar y retomar sin repetir pedidos.
"""

import argparse
import queue
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests

from src.db import get_connection
from src.descriptions import best_description, clean_description
from src.http import HEADERS

DELAY_SECONDS = 1.0
TIMEOUT_SECONDS = 15

# De mayor a menor calidad de sus descripciones (medido con paginas reales).
# Aldea y UpDown quedan al final: la primera mete avisos de despacho en el
# texto y la segunda solo trae datos sueltos. Jugones no se pide: su pagina
# solo tiene texto generico de la tienda (su listing ya trae jugadores/duracion).
STORE_PREFERENCE = [
    "DeMente Games", "VuduGaming", "Wargaming", "La Loseta", "Mana House", "Piedra Bruja",
    "Diverti", "Griffin Games", "El Patio Geek", "Café 2d6", "Aldea Juegos", "UpDown",
]
NEVER_FETCH = {"Jugones"}


def store_rank(name: str) -> int:
    return STORE_PREFERENCE.index(name) if name in STORE_PREFERENCE else len(STORE_PREFERENCE)


def load_products(cur):
    """Productos visibles sin descripcion util, con sus listings activos."""
    cur.execute(
        """
        select p.id::text, p.canonical_name, p.description,
               pl.id::text, pl.raw_title, pl.url, pl.description, pl.description_checked_at,
               s.name, coalesce(pps.store_count, 0)
        from products p
        join product_listings pl on pl.product_id = p.id and pl.is_active
        join stores s on s.id = pl.store_id and s.active
        left join product_price_stats pps on pps.product_id = p.id
        where p.hidden_at is null and p.merged_into is null and p.category = 'board_game'
        """
    )
    products = {}
    for pid, name, desc, lid, raw_title, url, ldesc, checked, store, store_count in cur.fetchall():
        entry = products.setdefault(pid, {"id": pid, "name": name, "description": desc, "store_count": store_count, "listings": []})
        entry["listings"].append(
            {"id": lid, "title": raw_title, "url": url, "description": ldesc, "checked": checked, "store": store}
        )
    for p in products.values():
        p["listings"].sort(key=lambda l: store_rank(l["store"]))
    return products


class Robots:
    """robots.txt por dominio, leido una sola vez. Si no se puede leer, se permite
    (la mayoria de estas tiendas ni tiene uno), igual que un navegador."""

    def __init__(self):
        self._cache: dict[str, RobotFileParser | None] = {}
        self._lock = threading.Lock()

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        with self._lock:
            if origin not in self._cache:
                parser = RobotFileParser()
                try:
                    response = requests.get(f"{origin}/robots.txt", headers=HEADERS, timeout=TIMEOUT_SECONDS)
                    if response.status_code == 200:
                        parser.parse(response.text.splitlines())
                        self._cache[origin] = parser
                    else:
                        self._cache[origin] = None
                except requests.RequestException:
                    self._cache[origin] = None
            parser = self._cache[origin]
        return parser is None or parser.can_fetch(HEADERS["User-Agent"], url)


def fetch_page(url: str) -> str | None:
    """Una pagina, con un reintento solo para errores transitorios (timeout, 5xx).
    Un 404 o 403 no se reintenta: no va a cambiar."""
    for attempt in range(2):
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SECONDS)
        except requests.RequestException:
            time.sleep(2)
            continue
        if response.status_code == 200:
            return response.text
        if response.status_code < 500:
            return None
        time.sleep(2)
    return None


def work_store(store: str, tasks: list[dict], results: queue.Queue, robots: Robots):
    """Pide las paginas de una tienda, de a una, con pausa entre pedidos."""
    for task in tasks:
        if robots.allowed(task["url"]):
            page = fetch_page(task["url"])
            text = best_description(page, task["title"], store) if page else None
            outcome = "ok" if text else ("sin_texto" if page else "sin_pagina")
        else:
            text, outcome = None, "robots"
        results.put({**task, "store": store, "text": text, "outcome": outcome})
        time.sleep(DELAY_SECONDS)


def revalidate(conn, dry_run: bool):
    """Reaplica las reglas de limpieza a las descripciones ya guardadas.

    Se corre cuando se descubre un tipo nuevo de relleno: lo que ya no pasa queda sin
    descripcion (y la proxima pasada prueba con otra tienda); lo que cambia por el
    recorte de una oracion se actualiza.
    """
    with conn.cursor() as cur:
        cur.execute(
            "select id, canonical_name, description, description_source from products where description is not null"
        )
        rows = cur.fetchall()
        removed = changed = 0
        for pid, name, description, source in rows:
            cleaned = clean_description(description, name, source)
            if cleaned == description:
                continue
            if cleaned is None:
                removed += 1
                new_source = None
            else:
                changed += 1
                new_source = source
            if not dry_run:
                cur.execute(
                    "update products set description = %s, description_source = %s where id = %s",
                    (cleaned, new_source, pid),
                )
        if not dry_run:
            conn.commit()
    print(f"Revisadas: {len(rows)} | quedan sin descripcion: {removed} | recortadas: {changed}"
          + ("  (SIMULACION: no se guardo nada)" if dry_run else ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--revalidate", action="store_true", help="reaplica las reglas de limpieza a lo ya guardado")
    parser.add_argument("--limit", type=int, default=None, help="maximo de paginas a pedir en esta corrida")
    parser.add_argument("--dry-run", action="store_true", help="no guarda nada; muestra lo que encontraria")
    parser.add_argument("--skip-stores", default="", help="tiendas a no pedir, separadas por coma (UpDown bloquea a GitHub)")
    args = parser.parse_args()
    skip = NEVER_FETCH | {s.strip() for s in args.skip_stores.split(",") if s.strip()}

    conn = get_connection()
    try:
        if args.revalidate:
            revalidate(conn, args.dry_run)
            return
        with conn.cursor() as cur:
            products = load_products(cur)
        print(f"Productos visibles: {len(products)}")

        # Fase 1: adoptar descripciones que ya traen los listings (sin pedidos).
        adopted, pending = [], []
        for p in products.values():
            if clean_description(p["description"], p["name"]):
                continue  # ya tiene una util
            found = next(
                (
                    (text, l["store"])
                    for l in p["listings"]
                    if (text := clean_description(l["description"], l["title"], l["store"]))
                ),
                None,
            )
            if found:
                adopted.append((p["id"], *found))
            else:
                pending.append(p)
        print(f"Sin descripcion util: {len(adopted) + len(pending)} | adoptadas de listings: {len(adopted)}")

        # Fase 2: pedir una pagina por producto. Primero los mas comparables
        # (mas tiendas), que son los que mas se miran.
        pending.sort(key=lambda p: -p["store_count"])
        by_store = defaultdict(list)
        total = 0
        for p in pending:
            if args.limit is not None and total >= args.limit:
                break
            listing = next((l for l in p["listings"] if l["store"] not in skip and l["checked"] is None), None)
            if listing:
                by_store[listing["store"]].append(
                    {"product_id": p["id"], "listing_id": listing["id"], "url": listing["url"], "title": listing["title"], "name": p["name"]}
                )
                total += 1
        print(f"Paginas a pedir: {total} en {len(by_store)} tiendas "
              + ", ".join(f"{s}: {len(t)}" for s, t in sorted(by_store.items())))

        with conn.cursor() as cur:
            if not args.dry_run:
                for pid, text, store in adopted:
                    cur.execute("update products set description = %s, description_source = %s where id = %s", (text, store, pid))
                conn.commit()

            results: queue.Queue = queue.Queue()
            robots = Robots()
            counts = defaultdict(int)
            started = time.time()
            with ThreadPoolExecutor(max_workers=max(1, len(by_store))) as pool:
                futures = [pool.submit(work_store, s, tasks, results, robots) for s, tasks in by_store.items()]
                done = 0
                while done < total:
                    try:
                        r = results.get(timeout=30)
                    except queue.Empty:
                        if all(f.done() for f in futures):
                            break
                        continue
                    done += 1
                    counts[r["outcome"]] += 1
                    if args.dry_run:
                        if r["text"] and counts["ok"] <= 40:
                            print(f"  [{r['store']}] {r['name']}\n      {r['text']}")
                    else:
                        cur.execute("update product_listings set description_checked_at = now() where id = %s", (r["listing_id"],))
                        if r["text"]:
                            cur.execute(
                                "update products set description = %s, description_source = %s where id = %s",
                                (r["text"], r["store"], r["product_id"]),
                            )
                        if done % 50 == 0:
                            conn.commit()
                    if done % 100 == 0:
                        print(f"  {done}/{total} ({time.time() - started:.0f}s) {dict(counts)}", flush=True)
            if not args.dry_run:
                conn.commit()

        print(f"\nListo en {time.time() - started:.0f}s. Resultado: {dict(counts)}"
              + ("  (SIMULACION: no se guardo nada)" if args.dry_run else ""))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
