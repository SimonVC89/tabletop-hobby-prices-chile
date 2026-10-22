"""Formato del resumen de ofertas por Telegram."""

from src.send_telegram_digest import build_digest_text, group_by_game


def offer(product: str, store: str, price: int, pct: float) -> dict:
    return {
        "product_id": product, "canonical_name": product, "store_name": store, "price_clp": price,
        "discount_pct": pct, "url": f"https://{store.lower().replace(' ', '')}.cl/{product.lower()}",
    }


def test_un_juego_en_dos_tiendas_sale_una_vez():
    text = build_digest_text([
        offer("Llama", "Aldea Juegos", 10392, 20.0),
        offer("Llama", "DeMente Games", 10392, 20.0),
        offer("Azul", "Jugones", 20000, 30.0),
    ])
    assert text.count("Llama -") == 1
    assert "También en DeMente Games: $10.392 (20.0% off)" in text
    assert "https://dementegames.cl/llama" in text
    # Numerado por juego: Azul (30%) primero y Llama segundo, sin un tercer item.
    assert "1. Azul" in text and "2. Llama" in text and "3." not in text


def test_la_mejor_oferta_va_arriba_y_define_la_seccion():
    text = build_digest_text([
        offer("Catan", "Tienda A", 20000, 25.0),
        offer("Catan", "Tienda B", 12000, 55.0),
    ])
    assert text.startswith("🔥 Ofertas destacadas")
    assert "1. Catan - $12.000 (55.0% off, Tienda B)" in text
    assert "También en Tienda A: $20.000 (25.0% off)" in text
    assert "Otras ofertas" not in text


def test_grupos_de_mayor_a_menor_descuento():
    groups = group_by_game([
        offer("A", "T1", 100, 21.0), offer("B", "T1", 100, 40.0), offer("A", "T2", 100, 35.0),
    ])
    assert [[o["store_name"] for o in g] for g in groups] == [["T1"], ["T2", "T1"]]
    assert [g[0]["product_id"] for g in groups] == ["B", "A"]


def test_el_tope_cuenta_juegos():
    offers = [offer(f"Juego{i}", "T", 1000, 25.0) for i in range(20)]
    text = build_digest_text(offers)
    assert "...y 5 juegos mas en oferta." in text   # TOP_N_OTRAS = 15


def test_sin_ofertas_no_hay_resumen():
    assert build_digest_text([]) is None
