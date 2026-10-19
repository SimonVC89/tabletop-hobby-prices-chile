"""Detecta productos que probablemente son el mismo juego partido en varios.

El match_key solo junta titulos con exactamente las mismas palabras, asi que
"Catan", "Catan Basico" y "Catan El Juego" quedan como tres productos. Este
script busca candidatos a fusionar y escribe un informe para revision humana;
no modifica la base.

    python -m src.matching.find_duplicates      # escribe duplicados_revision.md (+ .json)

El .json guarda los mismos candidatos con sus ids de producto: merge_duplicates
lo usa para aplicar exactamente lo que se reviso, aunque la base haya cambiado
entre medio (el cron corre a diario).

Dos senales:
- Clave nucleo: el match_key sin palabras que no cambian el juego ("basico",
  "el juego", "nueva edicion", "trilingue"...). Misma clave nucleo = candidato
  fuerte. La lista es conservadora a proposito: "junior", "deluxe", "duelo",
  "cartas", "expansion" o numeros nunca se quitan.
- Embeddings: titulos casi identicos en significado que la clave no capta
  (orden distinto, abreviaturas). Candidato debil.

Y dos alertas en contra, que se muestran en el informe:
- La misma tienda vende ambos productos: suele indicar que son distintos
  (base y deluxe, ediciones distintas).
- Precios muy diferentes entre ambos.
"""

import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import permutations
from pathlib import Path

import numpy as np
from pgvector.psycopg2 import register_vector

from src.db import get_connection
from src.matching.normalize import canonical

REPORT_PATH = Path(__file__).resolve().parents[2] / "duplicados_revision.md"
DECISIONS_PATH = REPORT_PATH.with_suffix(".json")

# Palabras que no distinguen un juego de otro cuando son la UNICA diferencia
# entre dos titulos. No se agregan aqui palabras que si cambian el producto.
SOFT_NOISE = {
    "el", "la", "los", "las", "the", "de", "del", "y", "para",
    "juego", "basico", "basica", "clasico", "original",
    # "revisada" NO va aqui: en Arkham Horror LCG la edicion revisada es otro
    # producto y conviven en las tiendas mientras la original se agota.
    "edicion", "nueva", "version",
    # Idioma: el proyecto agrupa ediciones en distintos idiomas (ver
    # normalize.NOISE_WORDS). Piedra Bruja marca las inglesas con "ING".
    "castellano", "espanola", "trilingue", "bilingue", "multilingue", "ing",
    "mesa", "board", "game",
}

EMBEDDING_THRESHOLD = 0.95
PRICE_RATIO_WARNING = 1.5
# Que tan parecidas deben ser dos palabras para tratarlas como la misma
# escrita distinto (difflib, 0..1): "volume"/"volumen" 0.92, "streaking"/"imploding" 0.44.
TYPO_SIMILARITY = 0.75

# Diferencias que en un par por embedding no descartan el candidato (se
# dejan para revision): El Patio Geek agrega la dificultad a los Exit y
# algunas tiendas marcan las expansiones con la palabra.
REVIEWABLE_EXTRAS = {"avanzado", "experto", "principiante", "expansion", "ampliacion"}


# Palabras que distinguen productos hermanos de nombre casi identico: si un
# titulo tiene una y el otro otra distinta del mismo conjunto, nunca son el
# mismo producto. En Arkham Horror LCG cada ciclo trae una expansion de
# campana y otra de investigadores que solo difieren en esa palabra.
EXCLUSIVE_MARKERS = [{"campana", "investigadores"}]


def core_key(match_key: str) -> str:
    words = {canonical(w) for w in match_key.split()}
    return " ".join(sorted(words - SOFT_NOISE))


def same_when_joined(only_a: set[str], only_b: set[str]) -> bool:
    """"brainbox" vs {"brain", "box"}: la misma palabra junta o separada."""
    if len(only_a) > 3 or len(only_b) > 3:
        return False
    joined_a = {"".join(p) for p in permutations(only_a)}
    return any("".join(p) in joined_a for p in permutations(only_b))


def conflicting_markers(words_a: set[str], words_b: set[str]) -> bool:
    return any(
        (words_a & markers) and (words_b & markers) and (words_a & markers) != (words_b & markers)
        for markers in EXCLUSIVE_MARKERS
    )


def plausible_pair(a, b) -> bool:
    """Descarta pares por embedding que casi seguro son productos distintos."""
    words_a, words_b = set(a["core"].split()), set(b["core"].split())
    if conflicting_markers(words_a, words_b):
        return False
    # Numeros distintos: "Black Stories 4" vs "5", "Pack #2" vs "#3".
    if {w for w in words_a if w.isdigit()} != {w for w in words_b if w.isdigit()}:
        return False
    # Uno es el otro mas un subtitulo: suele ser una expansion del juego base
    # ("Expedicion Ares" vs "Expedicion Ares: Crisis").
    for small, big in ((words_a, words_b), (words_b, words_a)):
        if small < big and not (big - small) <= REVIEWABLE_EXTRAS:
            return False
    # Cada uno tiene palabras propias: solo vale si son variantes de
    # escritura ("Undaunted"/"Unaunted", "Volume"/"Volumen"). Si no, son
    # productos hermanos ("Streaking Kittens" vs "Imploding Kittens").
    only_a, only_b = words_a - words_b, words_b - words_a
    if only_a and only_b and not same_when_joined(only_a, only_b):
        def has_twin(word, others):
            return any(SequenceMatcher(None, word, other).ratio() >= TYPO_SIMILARITY for other in others)

        if not all(has_twin(w, only_b) for w in only_a) or not all(has_twin(w, only_a) for w in only_b):
            return False
    return True


def load_products(cur):
    """Productos visibles con sus tiendas, precio de referencia y embedding promedio."""
    cur.execute("""
        select p.id::text, p.canonical_name, p.match_key, p.category::text
        from products p
        where p.hidden_at is null and p.category::text not like 'mtg_%%'
    """)
    products = {
        pid: {"id": pid, "name": name, "match_key": key, "category": cat, "stores": set(), "prices": [], "vectors": []}
        for pid, name, key, cat in cur.fetchall()
    }

    # Precio actual de cada listing activo (con o sin stock): sirve para
    # comparar el orden de magnitud entre candidatos.
    cur.execute("""
        select pl.product_id::text, s.name, cp.price_clp
        from product_listings pl
        join stores s on s.id = pl.store_id
        left join current_prices cp on cp.listing_id = pl.id
        where pl.is_active and pl.product_id is not null
    """)
    for pid, store, price in cur.fetchall():
        if pid in products:
            products[pid]["stores"].add(store)
            if price:
                products[pid]["prices"].append(price)

    cur.execute("""
        select product_id::text, title_embedding from product_listings
        where product_id is not null and title_embedding is not null
    """)
    for pid, emb in cur.fetchall():
        if pid in products:
            products[pid]["vectors"].append(emb)

    for p in products.values():
        p["price"] = int(np.median(p["prices"])) if p["prices"] else None
        p["core"] = core_key(p["match_key"] or "")
    return products


def warnings_for(group):
    """Alertas en contra de fusionar un grupo."""
    warnings = []
    seen = defaultdict(list)
    for p in group:
        for store in p["stores"]:
            seen[store].append(p["name"])
    shared = sorted(s for s, names in seen.items() if len(names) > 1)
    if shared:
        warnings.append(f"misma tienda vende varios: {', '.join(shared)}")
    prices = [p["price"] for p in group if p["price"]]
    if len(prices) > 1 and max(prices) / min(prices) > PRICE_RATIO_WARNING:
        warnings.append(f"precios muy distintos (x{max(prices) / min(prices):.1f})")
    return warnings


def find_core_groups(products):
    by_core = defaultdict(list)
    for p in products.values():
        if p["core"]:
            by_core[(p["category"], p["core"])].append(p)
    return [g for g in by_core.values() if len(g) > 1]


def find_embedding_pairs(products, already_grouped):
    """Pares con embeddings casi identicos que la clave nucleo no junto."""
    candidates = [p for p in products.values() if p["vectors"] and p["category"] == "board_game"]
    ids = [p["id"] for p in candidates]
    matrix = np.array([np.mean(p["vectors"], axis=0) for p in candidates], dtype=np.float32)
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)

    pairs = []
    for i in range(len(ids)):
        scores = matrix[i + 1:] @ matrix[i]
        for offset in np.nonzero(scores >= EMBEDDING_THRESHOLD)[0]:
            j = i + 1 + offset
            a, b = candidates[i], candidates[j]
            if a["core"] == b["core"] or {a["id"], b["id"]} <= already_grouped or not plausible_pair(a, b):
                continue
            pairs.append((float(scores[offset]), a, b))
    pairs.sort(key=lambda t: -t[0])
    return pairs


def describe(p):
    price = f"${p['price']:,}".replace(",", ".") if p["price"] else "sin precio"
    stores = ", ".join(sorted(p["stores"])) or "sin listings activos"
    return f"**{p['name']}** — {price} — {stores}"


def main():
    conn = get_connection()
    register_vector(conn)
    try:
        with conn.cursor() as cur:
            products = load_products(cur)
    finally:
        conn.close()

    groups = find_core_groups(products)
    groups.sort(key=lambda g: (-len(g), g[0]["core"]))
    grouped_ids = {p["id"] for g in groups for p in g}
    pairs = find_embedding_pairs(products, grouped_ids)

    # Cada candidato con un id estable dentro del informe: A = clave nucleo,
    # B = embeddings. Los sin alertas se fusionan por defecto; los con
    # alertas, no. La revision solo marca excepciones.
    candidates = [(f"A{n}", g, None) for n, g in enumerate(groups, 1)]
    candidates += [(f"B{n}", [a, b], score) for n, (score, a, b) in enumerate(pairs, 1)]
    merge = [c for c in candidates if not warnings_for(c[1])]
    hold = [c for c in candidates if warnings_for(c[1])]

    lines = [
        "# Duplicados de matching: revision",
        "",
        f"Productos revisados: {len(products)}. A = misma clave nucleo, B = embeddings casi identicos "
        f"(>= {EMBEDDING_THRESHOLD}).",
        "",
        f"## 1. Se fusionan salvo que digas lo contrario ({len(merge)})",
        "",
        "Indica los ids que NO son el mismo juego.",
        "",
    ]
    for cid, group, score in merge:
        names = " = ".join(p["name"] for p in sorted(group, key=lambda p: -len(p["stores"])))
        lines.append(f"- **{cid}** {names}" + (f" _(sim. {score:.2f})_" if score else ""))

    lines += [
        "",
        f"## 2. NO se fusionan salvo que digas lo contrario ({len(hold)})",
        "",
        "Tienen alertas (la misma tienda vende ambos, o precios muy distintos). Indica los ids que SI son el "
        "mismo juego.",
        "",
    ]
    for cid, group, score in hold:
        lines.append(f"### {cid} ⚠ {'; '.join(warnings_for(group))}" + (f" _(sim. {score:.2f})_" if score else ""))
        lines += [f"- {describe(p)}" for p in sorted(group, key=lambda p: -len(p["stores"]))]
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    decisions = [
        {
            "id": cid,
            "merge_by_default": not warnings_for(group),
            "products": [{"id": p["id"], "name": p["name"]} for p in group],
        }
        for cid, group, _ in candidates
    ]
    DECISIONS_PATH.write_text(json.dumps(decisions, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Candidatos: {len(candidates)} | se fusionan por defecto: {len(merge)} | en espera: {len(hold)}")
    print(f"Informe: {REPORT_PATH}")


if __name__ == "__main__":
    main()
