"""O serviço NOVO: modelo limpo, banco próprio. Aceita injeção de falha para o game day (POST /admin/falha)."""
import asyncio
import os
import random

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

URL = os.environ.get("URL_NOVO", "postgresql://luna:luna@postgres:5432/novo")
app = FastAPI(title="LunaLog novo")
falha = {"pct": 0, "atraso_ms": 0}


class Entrega(BaseModel):
    id: str
    status: str
    previsao: str
    valor_centavos: int
    transportadora_id: str


async def injetar():
    if falha["atraso_ms"]:
        await asyncio.sleep(falha["atraso_ms"] / 1000)
    if falha["pct"] and random.random() * 100 < falha["pct"]:
        raise HTTPException(500, "falha injetada para o game day")


@app.get("/entregas/{entrega_id}")
async def obter(entrega_id: str):
    await injetar()
    with psycopg.connect(URL) as c:
        l = c.execute("SELECT id, status, previsao, valor_centavos, transportadora_id FROM entregas WHERE id = %s", (entrega_id,)).fetchone()
    if l is None:
        raise HTTPException(404, "nao encontrada")
    return {"id": l[0], "status": l[1], "previsao": l[2].isoformat(), "valor_centavos": l[3], "transportadora_id": l[4]}


@app.put("/entregas/{entrega_id}")
async def gravar(entrega_id: str, e: Entrega, origem: str = "gateway"):
    await injetar()
    with psycopg.connect(URL, autocommit=True) as c:
        c.execute("INSERT INTO entregas (id, status, previsao, valor_centavos, transportadora_id, origem) VALUES (%s, %s, %s, %s, %s, %s) "
                  "ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, previsao = EXCLUDED.previsao, valor_centavos = EXCLUDED.valor_centavos, "
                  "transportadora_id = EXCLUDED.transportadora_id, origem = EXCLUDED.origem, atualizado_em = now()",
                  (entrega_id, e.status, e.previsao, e.valor_centavos, e.transportadora_id, origem))
    return {"ok": True}


@app.post("/admin/falha")
def configurar_falha(pct: int = 0, atraso_ms: int = 0):
    falha["pct"], falha["atraso_ms"] = pct, atraso_ms
    return falha
