"""Elige el nombre que se le muestra al usuario para cada producto.

Antes era "el titulo mas largo del grupo", que premiaba al mas ruidoso
(ej. "Terraforming Mars Expedicion Ares - Español" sobre la version que
escriben igual tres tiendas: "Terraforming Mars: Expedición Ares").

Ahora:
1. Se limpia cada titulo de sufijos de tienda (" - Español",
   " - Juego de mesa", " ESP", "(Inglés)"): el producto agrupa ediciones
   en varios idiomas, asi que mostrar uno en el nombre seria engañoso.
2. Gana el titulo limpio que escriben mas tiendas.
3. Desempates: con tildes (español bien escrito) > no todo en mayusculas
   > mas corto (menos ruido).
Se recalcula en cada corrida, porque al entrar tiendas nuevas al grupo el
mejor nombre puede cambiar.
"""

import re
from collections import defaultdict

from src.db import get_connection

_SUFFIXES = [
    re.compile(r"\s*\((en )?(espa[ñn]ol|ingl[eé]s)\)\s*$", re.I),
    re.compile(r"\s*[-–—:]\s*(juego de mesa|espa[ñn]ol|ingl[eé]s)\s*$", re.I),
    re.compile(r"\s+(esp|espa[ñn]ol)\s*$", re.I),
]
_ROMAN = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)$")


def clean_title(title: str) -> str:
    text = re.sub(r"\s+", " ", title).strip()
    previous = None
    while previous != text:
        previous = text
        for pattern in _SUFFIXES:
            text = pattern.sub("", text).strip()
        text = text.rstrip(" -–—:").strip()
    return text or title.strip()


def soften_caps(title: str) -> str:
    """'LEALTAD CERO' -> 'Lealtad Cero' (solo si viene todo en mayusculas)."""
    if not title.isupper():
        return title
    words = []
    for word in title.split(" "):
        if _ROMAN.match(word) or any(ch.isdigit() for ch in word) or len(word) <= 1:
            words.append(word)
        else:
            words.append(word[0] + word[1:].lower())
    return " ".join(words)


def choose_display_name(titles_by_store: dict[str, set[str]]) -> str:
    votes = defaultdict(set)
    for store, titles in titles_by_store.items():
        for t in titles:
            votes[clean_title(t)].add(store)

    def rank(title: str):
        has_accents = any(ord(ch) > 127 and ch.isalpha() for ch in title)
        return (len(votes[title]), has_accents, not title.isupper(), -len(title))

    return soften_caps(max(votes, key=rank))


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                select p.id, p.canonical_name, s.name, pl.raw_title
                from products p
                join product_listings pl on pl.product_id = p.id
                join stores s on s.id = pl.store_id
            """)
            groups = defaultdict(lambda: defaultdict(set))
            current = {}
            for pid, canonical, store, raw_title in cur.fetchall():
                groups[pid][store].add(raw_title)
                current[pid] = canonical

        changes = 0
        with conn.cursor() as cur:
            for pid, titles_by_store in groups.items():
                name = choose_display_name(titles_by_store)
                if name != current[pid]:
                    changes += 1
                    cur.execute("update products set canonical_name = %s where id = %s", (name, pid))
        conn.commit()
        print(f"Productos: {len(groups)} | nombres cambiados: {changes}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
