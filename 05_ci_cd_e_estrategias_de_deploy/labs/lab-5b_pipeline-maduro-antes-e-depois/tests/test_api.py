import pytest
from fastapi.testclient import TestClient

from main import app, calcular_frete

cliente = TestClient(app)


def test_saude():
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_entrega_existente():
    r = cliente.get("/entregas/E-100")
    assert r.status_code == 200
    assert r.json() == {"id": "E-100", "status": "em_rota"}


def test_entrega_inexistente():
    assert cliente.get("/entregas/E-999").status_code == 404


def test_frete_calculado():
    # 8,00 fixo + 10 kg x 1,50 + 100 km x 0,90 = 113,00
    assert calcular_frete(10, 100) == 113.00
    assert cliente.get("/frete", params={"peso_kg": 10, "distancia_km": 100}).json() == {"frete": 113.0}


def test_frete_com_valor_invalido():
    with pytest.raises(ValueError):
        calcular_frete(0, 100)
    assert cliente.get("/frete", params={"peso_kg": -1, "distancia_km": 10}).status_code == 422
