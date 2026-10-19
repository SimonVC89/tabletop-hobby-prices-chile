"""Seleccion de "Bajaron en las ultimas 24 horas" para la pagina de Inicio."""

from datetime import datetime, timezone

from src.export_frontend_snapshot import select_price_drops

WHEN = datetime(2026, 10, 19, 15, 44, tzinfo=timezone.utc)


def row(product: str, previous: int, price: int, store: str = "Tienda") -> dict:
    return {
        "product_id": product, "canonical_name": product, "image_url": None, "store_name": store,
        "url": f"https://x.cl/{product}", "previous_price": previous, "price": price, "changed_at": WHEN,
    }


def test_descarta_bajas_menores_al_umbral():
    drops = select_price_drops([row("A", 10000, 9600), row("B", 10000, 9500)], min_pct=5)
    assert [d["productName"] for d in drops] == ["B"]


def test_un_juego_aparece_una_vez_con_su_mayor_baja():
    drops = select_price_drops([row("A", 10000, 9000, "T1"), row("A", 10000, 7000, "T2")])
    assert len(drops) == 1
    assert drops[0]["storeName"] == "T2" and drops[0]["dropPct"] == 30.0


def test_orden_de_mayor_a_menor_y_tope():
    data = [row(str(i), 10000, 10000 - 100 * (i + 5)) for i in range(20)]
    drops = select_price_drops(data, limit=12)
    assert len(drops) == 12
    assert drops[0]["dropPct"] >= drops[-1]["dropPct"]


def test_formato_del_contrato():
    (drop,) = select_price_drops([row("Catan", 29990, 24990)])
    assert drop == {
        "productId": "Catan", "productName": "Catan", "imageUrl": None, "storeName": "Tienda",
        "listingUrl": "https://x.cl/Catan", "previousPrice": 29990, "price": 24990,
        "dropPct": 16.7, "changedAt": WHEN.isoformat(),
    }
