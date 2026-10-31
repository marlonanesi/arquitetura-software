"""Dependência externa simulada: responde rápido e sempre bem.
É o Toxiproxy, entre o serviço de cotação e esta dependência, que injeta a falha."""
import asyncio
import os

from fastapi import FastAPI

NOME = os.environ.get("NOME", "dependencia")
LATENCIA = int(os.environ.get("LATENCIA_MS", "40")) / 1000

app = FastAPI(title=NOME)


@app.get("/rota")
async def rota(origem: str = "A", destino: str = "B"):
    await asyncio.sleep(LATENCIA)
    return {"origem": origem, "destino": destino, "distancia_km": 42.5, "fonte": NOME}


@app.post("/enviar")
async def enviar():
    await asyncio.sleep(LATENCIA)
    return {"enviado": True, "fonte": NOME}
