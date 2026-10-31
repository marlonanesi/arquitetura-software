"""Serviço de entregas: grava a entrega e chama a roteirização, em cadeia síncrona."""
import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import COL_STATUS, conectar

URL_ROTEIRIZACAO = os.environ.get("URL_ROTEIRIZACAO", "http://roteirizacao:8000")
app = FastAPI(title="LunaLog distribuido: entregas")
http = httpx.Client(timeout=3.0)


class NovaEntrega(BaseModel):
    codigo: str
    destino: str


@app.post("/entregas", status_code=201)
def criar(e: NovaEntrega):
    # 1. grava a entrega e CONFIRMA a transação (ela já é visível para todos)
    with conectar() as conn:
        entrega_id = conn.execute(
            f"INSERT INTO entregas (codigo, destino, {COL_STATUS}) VALUES (%s, %s, 'criada') RETURNING id",
            (e.codigo, e.destino),
        ).fetchone()[0]

    # 2. chama o próximo serviço da cadeia. Se ele falhar, a entrega acima NÃO volta atrás.
    try:
        r = http.post(f"{URL_ROTEIRIZACAO}/rotas", json={"entrega_id": entrega_id, "destino": e.destino})
        r.raise_for_status()
    except httpx.HTTPError as erro:
        raise HTTPException(502, f"falha na cadeia: {erro.__class__.__name__}")
    return {"id": entrega_id, "codigo": e.codigo, "status": "roteirizada", **r.json()}


@app.get("/estado")
def estado():
    with conectar() as conn:
        def n(tabela: str) -> int:
            return conn.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]

        orfas = conn.execute(
            "SELECT count(*) FROM entregas e WHERE NOT EXISTS (SELECT 1 FROM notificacoes n WHERE n.entrega_id = e.id)"
        ).fetchone()[0]
        return {"entregas": n("entregas"), "rotas": n("rotas"), "notificacoes": n("notificacoes"),
                "entregas_sem_notificacao": orfas, "coluna_status": COL_STATUS}


@app.post("/admin/limpar")
def limpar():
    with conectar() as conn:
        conn.execute("TRUNCATE entregas, rotas, notificacoes RESTART IDENTITY")
    return {"ok": True}
