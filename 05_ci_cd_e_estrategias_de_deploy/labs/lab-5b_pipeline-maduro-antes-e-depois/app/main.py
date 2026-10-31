"""API de tracking da LunaLog: o serviço que o pipeline do lab 5B constrói, testa e implanta."""
import os

from fastapi import FastAPI, HTTPException

VERSAO = os.environ.get("VERSAO", "dev")

app = FastAPI(title="Tracking LunaLog", version=VERSAO)

ENTREGAS = {
    "E-100": {"id": "E-100", "status": "em_rota"},
    "E-200": {"id": "E-200", "status": "entregue"},
}


def calcular_frete(peso_kg: float, distancia_km: float) -> float:
    """Frete = taxa fixa + valor por quilo + valor por quilômetro."""
    if peso_kg <= 0 or distancia_km <= 0:
        raise ValueError("peso e distancia devem ser positivos")
    return round(8.0 + peso_kg * 1.5 + distancia_km * 0.9, 2)


@app.get("/saude")
def saude():
    return {"status": "ok", "versao": VERSAO}


@app.get("/entregas/{entrega_id}")
def entrega(entrega_id: str):
    if entrega_id not in ENTREGAS:
        raise HTTPException(404, "entrega nao encontrada")
    return ENTREGAS[entrega_id]


@app.get("/frete")
def frete(peso_kg: float, distancia_km: float):
    try:
        return {"frete": calcular_frete(peso_kg, distancia_km)}
    except ValueError as erro:
        raise HTTPException(422, str(erro))
