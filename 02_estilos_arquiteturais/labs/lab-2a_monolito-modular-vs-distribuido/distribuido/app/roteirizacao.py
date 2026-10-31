"""Serviço de roteirização: calcula a rota, grava e chama a notificação.

Repare no acoplamento pelo banco: este serviço grava direto na tabela "entregas", que pertence ao
serviço de entregas. Qualquer mudança nessa tabela afeta os dois.
"""
import os
import time

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import COL_STATUS, conectar

URL_NOTIFICACAO = os.environ.get("URL_NOTIFICACAO", "http://notificacao:8000")
app = FastAPI(title="LunaLog distribuido: roteirizacao")
http = httpx.Client(timeout=3.0)


class PedidoRota(BaseModel):
    entrega_id: int
    destino: str


@app.post("/rotas")
def atribuir(p: PedidoRota):
    time.sleep(0.02)   # cálculo da rota (simulado), igual ao do monólito modular
    motoristas = ["Ana", "Bruno", "Carla", "Diego"]
    indice = sum(map(ord, p.destino)) % len(motoristas)

    with conectar() as conn:
        conn.execute(
            "INSERT INTO rotas (entrega_id, sequencia, motorista) VALUES (%s, %s, %s)",
            (p.entrega_id, indice + 1, motoristas[indice]),
        )
        conn.execute(f"UPDATE entregas SET {COL_STATUS} = 'roteirizada' WHERE id = %s", (p.entrega_id,))

    try:
        r = http.post(f"{URL_NOTIFICACAO}/notificacoes", json={"entrega_id": p.entrega_id, "canal": "sms"})
        r.raise_for_status()
    except httpx.HTTPError as erro:
        raise HTTPException(502, f"falha na notificacao: {erro.__class__.__name__}")
    return {"motorista": motoristas[indice]}
