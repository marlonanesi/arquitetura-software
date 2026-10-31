"""Serviço de entregas da LunaLog (lab 5E).

A mesma imagem roda como v1 ou v2, conforme a variável VERSAO:

  v1 : lê e grava a coluna  nome_cliente        (nome antigo)
  v2 : lê e grava a coluna  destinatario_nome   (nome novo)

É a diferença entre as duas versões que a migração de schema precisa suportar
enquanto as duas estiverem em execução ao mesmo tempo.
"""
import os

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from psycopg_pool import ConnectionPool

VERSAO = os.environ.get("VERSAO", "v1")
COLUNA = "nome_cliente" if VERSAO == "v1" else "destinatario_nome"

pool = ConnectionPool(os.environ["DATABASE_URL"], min_size=1, max_size=10, kwargs={"autocommit": True}, open=True)
app = FastAPI(title=f"Entregas LunaLog {VERSAO}")


class NovaEntrega(BaseModel):
    cliente: str


class AtualizaCliente(BaseModel):
    cliente: str


def marcar(response: Response):
    response.headers["X-Versao"] = VERSAO


@app.post("/entregas", status_code=201)
def criar(e: NovaEntrega, response: Response):
    marcar(response)
    with pool.connection() as conn:
        linha = conn.execute(
            f"INSERT INTO entregas ({COLUNA}, status) VALUES (%s, 'criada') RETURNING id", (e.cliente,)
        ).fetchone()
    return {"id": linha[0], "cliente": e.cliente, "versao": VERSAO}


@app.get("/entregas/{entrega_id}")
def ler(entrega_id: int, response: Response):
    marcar(response)
    with pool.connection() as conn:
        linha = conn.execute(f"SELECT id, {COLUNA}, status FROM entregas WHERE id = %s", (entrega_id,)).fetchone()
    if linha is None:
        raise HTTPException(404, "entrega nao encontrada")
    return {"id": linha[0], "cliente": linha[1], "status": linha[2], "versao": VERSAO}


@app.patch("/entregas/{entrega_id}/cliente")
def atualizar(entrega_id: int, a: AtualizaCliente, response: Response):
    marcar(response)
    with pool.connection() as conn:
        n = conn.execute(f"UPDATE entregas SET {COLUNA} = %s WHERE id = %s", (a.cliente, entrega_id)).rowcount
    if n == 0:
        raise HTTPException(404, "entrega nao encontrada")
    return {"id": entrega_id, "cliente": a.cliente, "versao": VERSAO}
