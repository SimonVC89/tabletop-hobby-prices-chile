"""Reintento de las tiendas que fallaron en la corrida del cron."""

from src.retry_failed_stores import parse_outcomes, retry_failed

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
