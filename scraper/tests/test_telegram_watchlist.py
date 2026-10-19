"""Reglas de aviso del seguimiento de juegos y formato de los mensajes."""

import re

import pytest

from src.telegram_watchlist import (
    MAX_COMMAND_LENGTH,
    WATCH_DROP_PCT,
    _forms,
    _norm,
    code_of,
    correct_terms,
    decide,
    format_watch_section,
    match_catalog,
    more_command,
    narrowing_words,
    parse_more_command,
)


def item(name: str, price: int | None = 10000, stores: int = 3) -> dict:
    """Un juego del catalogo, con la misma forma que arma _load_catalog."""
    normalized = _norm(name)
    return {
        "id": name, "name": name, "stores": stores, "price": price,
        "normalized": normalized, "forms": [_forms(tok) for tok in normalized.split()],
    }


CATALOG = [
    item("Catan"),
    item("Catan Navegantes"),
    item("Catan: Navegantes de Catan Exp. 5-6 Jug."),
    item("Catan Ciudades Y Caballeros Ampliación 5-6 Jugadores"),
    item("Catan Junior", price=None),
    item("Cares Of Pandora"),
    item("Arkham Horror LCG"),
    item("Arkham Horror LCG: El Círculo Roto exp Campaña"),
    item("Arkham Horror LCG La Fiesta del Valle de la Cicuta exp. campaña"),
    item("Arkham Horror LCG La Fiesta del Valle de la Cicuta exp. investigadores"),
    item("Terraforming Mars: Expedición Ares"),
]


def names(terms: str) -> list[str]:
    return [m["name"] for m in match_catalog([dict(i) for i in CATALOG], _norm(terms).split())]


def test_umbral_de_baja():
    assert WATCH_DROP_PCT == 5


@pytest.mark.parametrize(
    "prev_in_stock, ref, best, expected",
    [
        (True, 10000, 10000, (None, 10000, True)),   # sin cambios
        (True, 10000, 9600, (None, 10000, True)),    # baja 4%: no alcanza
        (True, 10000, 9500, ("drop", 9500, True)),   # baja 5%: avisa
        (True, 10000, 7000, ("drop", 7000, True)),   # baja grande
        (True, 10000, 14000, (None, 10000, True)),   # sube: no avisa y la referencia no se mueve
        (True, 10000, None, (None, 10000, False)),   # se agota: silencioso
        (False, 10000, 12000, ("restock", 12000, True)),  # vuelve el stock
        (False, None, None, (None, None, False)),    # sigue agotado
        (False, None, 8000, ("restock", 8000, True)),     # se seguia agotado y aparece
    ],
)
def test_decide(prev_in_stock, ref, best, expected):
    assert decide(prev_in_stock, ref, best) == expected


def test_dos_bajadas_chicas_seguidas_no_se_pierden():
    """La referencia no baja con las bajadas que no avisan: 3% + 3% termina avisando."""
    event, ref, stock = decide(True, 10000, 9700)
    assert event is None and ref == 10000
    event, ref, stock = decide(stock, ref, 9400)  # 6% bajo la referencia original
    assert event == "drop" and ref == 9400


def test_codigo_corto_tocable():
    code = code_of("c827edbb-d4df-4055-9e04-a95ed0070531")
    assert code == "c827edbb"
    # Telegram solo convierte en enlace un comando con letras, numeros y guion bajo.
    assert re.fullmatch(r"/seguir_[a-z0-9]+", f"/seguir_{code}")


# --- busqueda -------------------------------------------------------------

def test_cada_palabra_es_un_prefijo():
    assert "Catan Navegantes" in names("catan nav")
    assert "Arkham Horror LCG" in names("ark hor")


def test_no_busca_en_medio_de_una_palabra():
    """'ares' no debe traer 'Cares': antes era una busqueda por subcadena."""
    assert names("ares") == ["Terraforming Mars: Expedición Ares"]


def test_ignora_tildes_mayusculas_y_orden():
    assert names("CÍRCULO arkham") == ["Arkham Horror LCG: El Círculo Roto exp Campaña"]
    assert names("navegantes catan") == names("catan navegantes")


def test_entiende_sinonimos():
    # "ampliacion", "expansion" y "exp" son lo mismo; "jug" y "jugadores", tambien.
    both = {"Catan: Navegantes de Catan Exp. 5-6 Jug.", "Catan Ciudades Y Caballeros Ampliación 5-6 Jugadores"}
    assert set(names("catan expansion 5 6 jugadores")) == both
    assert set(names("catan ampliacion 5-6 jug")) == both


def test_orden_de_los_resultados():
    result = names("catan")
    assert result[0] == "Catan"                     # nombre exacto primero
    assert result.index("Catan Junior") == len(result) - 1   # sin stock al final
    assert result.index("Catan Navegantes") < result.index("Catan Ciudades Y Caballeros Ampliación 5-6 Jugadores")  # nombres cortos antes


def test_sin_coincidencias():
    assert names("zzzzqqq") == []


def test_corrige_errores_de_tipeo():
    assert correct_terms(CATALOG, ["catna"]) == ["catan"]
    assert correct_terms(CATALOG, ["arkam", "horror"]) == ["arkham", "horror"]


def test_no_corrige_lo_que_ya_existe_ni_las_palabras_cortas():
    assert correct_terms(CATALOG, ["nav"]) == ["nav"]        # es prefijo de "navegantes"
    assert correct_terms(CATALOG, ["ark"]) == ["ark"]        # muy corta para adivinar
    assert correct_terms(CATALOG, ["qwertyuiop"]) == ["qwertyuiop"]  # nada se le parece


def test_palabras_para_acotar_separan_los_resultados():
    arkham = [m for m in match_catalog([dict(i) for i in CATALOG], ["arkham"])]
    words = narrowing_words(arkham, ["arkham"])
    assert "campaña" in words                                # con tilde, como en los nombres
    assert "arkham" not in words and "horror" not in words   # ya estan en la busqueda


def test_palabras_para_acotar_no_repiten_singular_y_plural():
    matches = [item("X uno investigador"), item("X dos investigadores"), item("X tres investigadores"), item("X cuatro mazo")]
    words = narrowing_words(matches, ["x"])
    assert not ({"investigador", "investigadores"} <= set(words))


def test_el_comando_de_paginacion_ida_y_vuelta():
    command = more_command(2, ["arkham", "horror", "lcg"])
    assert command == "/mas_2_arkham_horror_lcg"
    assert parse_more_command(command.removeprefix("/mas_")) == (2, ["arkham", "horror", "lcg"])


def test_paginacion_con_busqueda_demasiado_larga_no_ofrece_enlace():
    assert more_command(2, ["terraforming", "mars", "expedicion", "ares", "descubrimiento", "crisis"]) is None
    assert MAX_COMMAND_LENGTH == 60


@pytest.mark.parametrize("rest", ["x_arkham", "1_catan", "0_catan", "2", "2_", "_catan", ""])
def test_comandos_de_paginacion_invalidos(rest):
    assert parse_more_command(rest) is None


@pytest.mark.parametrize(
    "hour, expected",
    [
        (5, "mañana"), (11, "mañana"),
        (12, "tarde"), (13, "tarde"), (19, "tarde"),   # la corrida de la manana llego a salir a la 1 pm
        (20, "noche"), (23, "noche"),
    ],
)
def test_saludo_segun_la_hora_de_envio(hour, expected):
    from src.send_telegram_digest import greeting_for_hour

    assert expected in greeting_for_hour(hour)


def test_formato_del_aviso():
    text = format_watch_section(
        [
            {"event": "drop", "name": "Catan", "price": 24990, "previous": 29990, "store": "Aldea Juegos", "url": "https://x.cl/a"},
            {"event": "restock", "name": "Azul", "price": 39990, "previous": None, "store": "Jugones", "url": "https://x.cl/b"},
        ]
    )
    assert text.startswith("⭐ De tu lista:")
    assert "Catan bajó a $24.990 en Aldea Juegos (antes $29.990, -17%)" in text
    assert "Azul volvió a tener stock desde $39.990 en Jugones" in text
    assert "https://x.cl/a" in text and "https://x.cl/b" in text
