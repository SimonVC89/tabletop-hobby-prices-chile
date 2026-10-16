"""Clasifica productos: juego de mesa vs. accesorio, TCG, rol u otro.

Las tiendas mezclan en sus categorias de "juegos de mesa" cosas que no lo
son (protectores de cartas, boosters de TCG, naipes, libros de rol...).
No se borran: se clasifican, y ofertas/Telegram/frontend solo usan
category = 'board_game'. Asi es reversible y se puede recalibrar sin
volver a scrapear.

Criterios acordados:
- Complementos de UN juego especifico (expansiones, dados o insertos
  propios de un juego, upgrades) cuentan como juego de mesa: en juegos
  como Arkham Horror LCG son practicamente parte de jugarlo.
- Accesorio = solo lo generico (protectores, playmats, albumes, deck
  boxes, sets de dados genericos, insumos de pintura).
- Juegos de cartas si (Uno, Dobble...); naipes comunes no.

Uso:
    python -m src.matching.classify            # aplica
    python -m src.matching.classify --dry-run  # solo reporta
"""

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from src.db import get_connection
from src.matching.normalize import strip_accents

# Señales de que SI es un juego de mesa: ganan sobre cualquier regla.
BOARD_GAME_SIGNALS = re.compile(
    r"\b(juego de mesa|juego de cartas|card game|board game|boardgame|"
    r"monopoly|voynich|fabulas de peluche|stuffed fables|dungeon mayhem|"
    r"folded space|drunagor)\b"
)

# Orden importa: la primera regla que calza decide.
RULES: list[tuple[str, re.Pattern]] = [
    ("tcg", re.compile(
        r"\b(magic the gathering|mtg|yu-?gi-?oh|lorcana|flesh and blood|"
        r"one piece card|digimon|riftbound|altered|star wars unlimited|"
        r"pokemon (tcg|booster|sobre|elite trainer|etb|blister|mini tin|lata)|"
        r"(booster|sobre) (de )?pokemon|commander deck|collector booster|"
        r"draft booster|play booster|booster display|booster box)\b"
    )),
    ("rpg", re.compile(
        r"\b(juego de rol|manual del jugador|guia del (dungeon )?master|"
        r"manual de monstruos|player'?s handbook|dungeon master'?s guide|"
        r"monster manual|pathfinder (2|segunda)|pathfinder:|set de mapas|journeys through|"
        # D&D solo con terminos de libro/mapa: "D&D: Comienza la Aventura"
        # (Adventure Begins) es un juego de mesa familiar, no rol.
        r"(dungeons (and|&) dragons|d ?& ?d)\b.*\b(mapa|libro|guia|manual))\b"
    )),
    ("accessory", re.compile(
        r"\b(protector(es)?|sleeves?|fundas?|micas?|playmat|tapete|alfombrilla|"
        r"deck ?box|porta ?mazos?|portacartas|album|binder|carpeta|"
        r"set de \d+ dados|\d+ dados d\d+|d6 dice set|dice set \d+|dados de rol|"
        r"pintura|pincel|citadel|vallejo)\b"
    )),
    ("other", re.compile(
        r"\b(naipes?|baraja (inglesa|espanola)|bicycle|tarot|"
        # "N piezas" solo junto a puzzle: "Mikado Jumbo 31 Piezas" es un juego.
        r"rompecabezas|puzzle.*\d+ piezas|megabloks|rubik|cubo magico|speed ?cube|"
        r"funko|llavero|polera|taza)\b"
    )),
]

RECLASSIFIABLE = ("board_game", "accessory", "tcg", "rpg", "other")


def classify(title: str) -> str:
    text = strip_accents(title).lower()
    if BOARD_GAME_SIGNALS.search(text):
        return "board_game"
    for category, pattern in RULES:
        if pattern.search(text):
            return category
    return "board_game"


def main():
    dry_run = "--dry-run" in sys.argv
    conn = get_connection()
    try:
        # Se clasifica mirando los titulos de TODAS las tiendas del producto,
        # no solo el nombre visible: ese viene limpio (sin "- Juego de mesa"),
        # y esa frase es justamente una de las señales positivas.
        with conn.cursor() as cur:
            cur.execute(
                """
                select p.id, p.canonical_name, p.category::text,
                       string_agg(distinct pl.raw_title, ' | ')
                from products p join product_listings pl on pl.product_id = p.id
                where p.category::text = any(%s)
                group by p.id
                """,
                (list(RECLASSIFIABLE),),
            )
            products = cur.fetchall()

        classified = [(pid, name, old, classify(titles)) for pid, name, old, titles in products]
        changes = [c for c in classified if c[2] != c[3]]
        result = Counter(c[3] for c in classified)
        print(f"Productos evaluados: {len(products)} | resultado: {dict(result)}")
        print(f"Cambios de categoria: {len(changes)}")

        if dry_run:
            by_cat = defaultdict(list)
            for _, name, _, new in changes:
                by_cat[new].append(name)
            out = Path("clasificacion_revision.md")
            with out.open("w", encoding="utf-8") as f:
                for cat, names in sorted(by_cat.items()):
                    f.write(f"## {cat} ({len(names)})\n\n")
                    f.writelines(f"- {n}\n" for n in sorted(names))
                    f.write("\n")
            print(f"Dry-run: nada escrito en la base. Detalle en {out.resolve()}")
            return

        with conn.cursor() as cur:
            for pid, _, _, new in changes:
                cur.execute("update products set category = %s where id = %s", (new, pid))
        conn.commit()
        print("Listo.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
