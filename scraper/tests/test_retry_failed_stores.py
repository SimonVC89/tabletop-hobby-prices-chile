"""Reintento de las tiendas que fallaron en la corrida del cron."""

from datetime import datetime, timedelta, timezone

from src.retry_failed_stores import parse_outcomes, repeated_failures, retry_failed

NOW = datetime(2026, 10, 23, 23, 12, tzinfo=timezone.utc)  # 20:12 en Chile, fin de la corrida de las 19:17

OUTCOMES = """
src.ingest_laloseta=failure
src.ingest_dementegames=success
src.ingest_jugones=failure
"""


def test_lee_el_resultado_de_cada_tienda():
    assert parse_outcomes(OUTCOMES) == {
        "src.ingest_laloseta": "failure",
        "src.ingest_dementegames": "success",
        "src.ingest_jugones": "failure",
    }


def test_solo_reintenta_las_que_fallaron_y_espera_antes():
    calls, waits = [], []
    still = retry_failed(parse_outcomes(OUTCOMES), run=lambda m: calls.append(m) or True,
                         sleep=waits.append, waits=(120, 300))
    assert still == []
    assert calls == ["src.ingest_laloseta", "src.ingest_jugones"]
    assert waits == [120]  # se recuperaron al primer reintento: no espera el segundo


def test_una_tienda_que_se_recupera_al_segundo_intento():
    attempts = {"src.ingest_laloseta": 0}

    def run(module):
        attempts[module] += 1
        return attempts[module] == 2

    still = retry_failed({"src.ingest_laloseta": "failure"}, run=run, sleep=lambda s: None)
    assert still == []
    assert attempts["src.ingest_laloseta"] == 2


def test_la_que_sigue_fallando_se_informa():
    still = retry_failed({"src.ingest_laloseta": "failure"}, run=lambda m: False, sleep=lambda s: None)
    assert still == ["src.ingest_laloseta"]


def test_un_step_cancelado_o_saltado_tambien_se_reintenta():
    still = retry_failed({"src.ingest_x": "cancelled", "src.ingest_y": "skipped"}, run=lambda m: True,
                         sleep=lambda s: None)
    assert still == []


def test_sin_fallas_no_reintenta_ni_espera():
    waits = []
    still = retry_failed({"src.ingest_x": "success"}, run=lambda m: False, sleep=waits.append)
    assert still == [] and waits == []


def test_si_la_corrida_anterior_la_leyo_es_solo_advertencia():
    # Se leyo bien en la corrida de las 05:17 (~15 h antes): esta es la primera falla.
    seen = {"src.ingest_laloseta": NOW - timedelta(hours=14, minutes=50)}
    assert repeated_failures(["src.ingest_laloseta"], seen, NOW) == []


def test_si_fallo_tambien_la_anterior_es_error():
    # Ultima lectura buena hace ~24 h: fallaron la corrida de las 05:17 y esta.
    seen = {"src.ingest_laloseta": NOW - timedelta(hours=24)}
    assert repeated_failures(["src.ingest_laloseta"], seen, NOW) == ["src.ingest_laloseta"]


def test_sin_lecturas_registradas_es_error():
    assert repeated_failures(["src.ingest_x", "src.ingest_y"], {"src.ingest_y": None}, NOW) == [
        "src.ingest_x", "src.ingest_y"]


def test_cada_modulo_de_tienda_define_su_nombre():
    # last_seen_in_db busca la tienda por STORE_NAME del modulo src.ingest_*.
    import importlib
    import pathlib

    modules = sorted(p.stem for p in pathlib.Path("src").glob("ingest_*.py"))
    assert modules, "no se encontraron modulos src/ingest_*.py"
    for name in modules:
        assert importlib.import_module(f"src.{name}").STORE_NAME
