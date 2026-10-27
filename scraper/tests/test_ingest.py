"""Casos de una ingesta que no son "todo bien": tienda cerrada y 0 productos."""

import pytest

from src import http
from src.http import StoreClosedError, fetch_html
from src.ingest import NoProductsError, scrape


class FakeResponse:
    def __init__(self, url, status=200, text="<html></html>"):
        self.url, self.status_code, self.text = url, status, text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise http.requests.HTTPError(f"{self.status_code}")


def test_una_tienda_que_redirige_a_su_pagina_de_contrasena_esta_cerrada(monkeypatch):
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return FakeResponse("https://manahouse.cl/password")

    monkeypatch.setattr(http.requests, "get", get)
    with pytest.raises(StoreClosedError):
        fetch_html("https://manahouse.cl/collections/juegos-de-mesa")
    assert len(calls) == 1  # no es pasajero: no se reintenta


def test_una_pagina_normal_se_devuelve(monkeypatch):
    monkeypatch.setattr(http.requests, "get", lambda url, **kw: FakeResponse(url, text="<p>ok</p>"))
    assert fetch_html("https://tienda.cl/collections/juegos") == "<p>ok</p>"


def test_una_url_que_solo_contiene_password_no_es_cierre(monkeypatch):
    url = "https://tienda.cl/products/password-el-juego"
    monkeypatch.setattr(http.requests, "get", lambda u, **kw: FakeResponse(url, text="juego"))
    assert fetch_html(url) == "juego"


def test_tienda_cerrada_es_advertencia_y_no_guarda_nada(capsys):
    def closed():
        raise StoreClosedError("https://manahouse.cl/ redirige a https://manahouse.cl/password")

    assert scrape("Mana House", closed) is None
    assert "::warning::Mana House esta cerrada al publico" in capsys.readouterr().out


def test_cero_productos_con_la_tienda_abierta_es_falla():
    with pytest.raises(NoProductsError, match="Mana House: 0 productos"):
        scrape("Mana House", lambda: [])


def test_con_productos_los_devuelve():
    products = [{"title": "Catan"}]
    assert scrape("La Loseta", lambda: products) == products
