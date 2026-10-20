"""Reglas de aviso del seguimiento de juegos y formato de los mensajes.

La busqueda de /seguir se prueba en el backend (BotSearchTest.java), que es donde vive.
"""

import pytest

from src.telegram_watchlist import WATCH_DROP_PCT, decide, format_watch_section


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
