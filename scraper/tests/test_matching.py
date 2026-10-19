"""Normalizacion de titulos, deteccion de duplicados y sagas."""

import pytest

from src.export_frontend_snapshot import family_key
from src.matching.find_duplicates import core_key, plausible_pair
from src.matching.normalize import build_match_key


def core(name: str) -> str:
    return core_key(build_match_key(name))


def pair(a: str, b: str) -> bool:
    return plausible_pair({"core": core(a)}, {"core": core(b)})


def test_match_key_ignora_tildes_mayusculas_orden_e_idioma():
    assert build_match_key("Catán - Español") == build_match_key("CATAN")
    assert build_match_key("Juego de mesa Azul") == build_match_key("Azul")
    assert build_match_key("Dixit Origins") == build_match_key("Origins Dixit")


@pytest.mark.parametrize(
    "a, b",
    [
        ("Catan", "Catan Básico"),
        ("Catan", "Catan El Juego"),
        ("Dixit", "Dixit (Nueva Versión)"),
        ("Dominion (Segunda Edición)", "Dominion (2da Edición)"),
        ("Catan Ampliación 5-6 jugadores", "Catan Exp. 5-6 Jug."),
        ("Machi Koro 2da Edición", "Machi Koro Segunda Edición"),
    ],
)
def test_misma_clave_nucleo(a, b):
    assert core(a) == core(b)


@pytest.mark.parametrize(
    "a, b",
    [
        ("Machi Koro 2da Edición", "Machi Koro 2"),                # edicion vs secuela
        ("Arkham Horror LCG", "Arkham Horror LCG - Edición Revisada"),  # la revisada es otro producto
        ("Catan", "Catan Junior"),
        ("Black Stories 4", "Black Stories 5"),
    ],
)
def test_distinta_clave_nucleo(a, b):
    assert core(a) != core(b)


@pytest.mark.parametrize(
    "a, b",
    [
        ("Black Stories 4", "Black Stories 5"),                    # numeros distintos
        ("Streaking Kittens", "Imploding Kittens"),                # hermanos
        ("Terraforming Mars: Expedición Ares", "Terraforming Mars Expedición Ares: Crisis"),  # subtitulo = expansion
        ("Arkham Horror LCG La Fiesta exp. campaña", "Arkham Horror LCG La Fiesta exp. investigadores"),
    ],
)
def test_pares_que_no_se_fusionan(a, b):
    assert not pair(a, b)


@pytest.mark.parametrize(
    "a, b",
    [
        ("Undaunted: Stalingrad", "Unaunted: Stalingrad"),     # error de tipeo
        ("BrainBox Harry Potter", "Brain Box Harry Potter"),   # palabra junta o separada
        ("Oath: Crónica del Imperio", "Oath: Crónicas del Imperio"),
    ],
)
def test_pares_que_si_se_fusionan(a, b):
    assert pair(a, b)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Catan Junior", "catan"),
        ("Catán: Navegantes", "catan"),
        ("El Señor de los Anillos LCG", "senor"),
        ("7 Wonders Duel", "7 wonders"),
        ("Ark Nova", "ark nova"),
        ("Star Realms: Escenarios", "star realms"),   # prefijo ambiguo: dos palabras
        ("Star Wars Rivals", "star wars"),
        ("Juego de dados clásico", None),             # primera palabra generica
        ("Pack de cartas", None),
    ],
)
def test_clave_de_saga(name, expected):
    assert family_key(name) == expected
