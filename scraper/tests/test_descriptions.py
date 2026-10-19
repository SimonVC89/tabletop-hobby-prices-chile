"""Limpieza de descripciones: que se queda, que se descarta y que se recorta."""

from src.descriptions import MAX_LENGTH, MIN_LENGTH, best_description, clean_description

REAL = (
    "En Wingspan, un juego competitivo de producción y coleccionismo de aves, seréis unos "
    "apasionados de las aves que buscan descubrir y atraer a las mejores aves a sus reservas."
)


def test_conserva_una_descripcion_real():
    assert clean_description(REAL, "Wingspan") == REAL


def test_descarta_el_titulo_repetido():
    assert clean_description("Dominations - Español", "Dominations") is None
    assert clean_description("Juego de mesa Dragonkeepers — juego familiar", "Dragonkeepers") is None


def test_descarta_textos_demasiado_cortos():
    assert clean_description("Un juego de cartas.", "Otro nombre") is None
    assert MIN_LENGTH == 60


def test_descarta_el_texto_alternativo_de_la_imagen():
    alt = "Portada del juego de mesa 'Lost Cities: Exploradores' disponible en Mana House – Cartas, Exploración"
    assert clean_description(alt, "Lost Cities Exploradores") is None
    assert clean_description("Portada de la expansión 'Splendor: La Ruta de la Seda' para el juego base", "Splendor") is None


def test_descarta_avisos_legales_y_de_preventa():
    legal = "Esta compra no está sujeta al derecho a retracto, según el artículo 3 bis de la Ley 19.496"
    assert clean_description(legal, "Marvel Champions") is None
    preventa = (
        "No tiene fecha de llegada definitiva, se espera que sea este año 2026 o a comienzos de 2027. "
        "El precio de venta es estimado."
    )
    assert clean_description(preventa, "Forest Shuffle") is None


def test_descarta_listas_de_componentes():
    assert clean_description("COMPONENTES 1 libreta con el Mapa de Paris, 4 lápices de colores diferentes y más", "X") is None


def test_quita_solo_la_oracion_de_relleno():
    raw = (
        "El clásico Catan: construye, comercia y expande tus dominios en la isla para ganar la partida. "
        "Envío a todo Chile."
    )
    cleaned = clean_description(raw, "Catan")
    assert cleaned == "El clásico Catan: construye, comercia y expande tus dominios en la isla para ganar la partida."


def test_quita_la_oracion_que_nombra_a_la_tienda():
    raw = (
        "Descubre Wingspan: estrategia, aves únicas y combos elegantes para toda la mesa. "
        "Lo encuentras en Piedra Bruja con despacho rápido."
    )
    cleaned = clean_description(raw, "Wingspan", store_name="Piedra Bruja")
    assert "Piedra Bruja" not in cleaned
    assert cleaned.startswith("Descubre Wingspan")


def test_quita_emojis_y_html():
    raw = "<p>🌌 Terraforming Mars coloca a cada jugador al mando de una megacorporación empeñada en transformar Marte.</p>"
    cleaned = clean_description(raw, "Terraforming Mars")
    assert cleaned.startswith("Terraforming Mars coloca")
    assert "<" not in cleaned and "🌌" not in cleaned


def test_recorta_en_una_oracion_completa():
    sentence = "Esta es una oración de relleno bastante larga para probar el recorte del texto. "
    cleaned = clean_description(sentence * 10, "Nada")
    assert len(cleaned) <= MAX_LENGTH
    assert cleaned.endswith(".")


def test_recorta_en_una_palabra_si_no_hay_oracion_cercana():
    cleaned = clean_description("palabra " * 80, "Nada")
    assert len(cleaned) <= MAX_LENGTH + 1
    assert cleaned.endswith("…")


def test_best_description_prefiere_el_json_ld_y_salta_los_textos_inservibles():
    page = f"""
    <html><head>
      <meta property="og:description" content="Compra juegos de mesa en la tienda online líder de Santiago">
      <script type="application/ld+json">{{"@type": "Product", "description": "{REAL}"}}</script>
    </head></html>
    """
    assert best_description(page, "Wingspan", "Griffin Games") == REAL


def test_best_description_usa_la_meta_si_no_hay_json_ld():
    page = f'<html><head><meta property="og:description" content="{REAL}"></head></html>'
    assert best_description(page, "Wingspan", "DeMente Games") == REAL


def test_best_description_sin_nada_util_devuelve_none():
    assert best_description("<html><head></head></html>", "Algo", "Tienda") is None
