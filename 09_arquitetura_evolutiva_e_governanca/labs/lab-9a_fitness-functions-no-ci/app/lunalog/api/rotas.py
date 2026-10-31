"""Camada de API: HTTP. Fala com o domínio, nunca com a infraestrutura diretamente."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from lunalog.dominio import clientes, tarifas

app = FastAPI(title="LunaLog API", version="1.0.0")


class Frete(BaseModel):
    frete: float


class Cliente(BaseModel):
    id: str
    nome: str


@app.get("/saude")
def saude():
    return {"status": "ok"}


@app.get("/frete", response_model=Frete)
def frete(peso_kg: float, distancia_km: float, regiao: str = "sudeste"):
    try:
        return Frete(frete=tarifas.calcular_frete(peso_kg, distancia_km, regiao))
    except ValueError as erro:
        raise HTTPException(422, str(erro))


@app.get("/clientes/{cliente_id}", response_model=Cliente)
def cliente(cliente_id: str):
    dados = clientes.buscar_cliente(cliente_id)
    if dados is None:
        raise HTTPException(404, "cliente nao encontrado")
    return dados
