"""API de confirmação de entrega com DOIS caminhos para a mesma operação (lab 3D).

  POST /confirmacoes/direto   grava no banco dentro da requisição (síncrono)
  POST /confirmacoes/fila     publica uma mensagem e responde 202 (assíncrono); o worker grava depois

O banco tem uma capacidade finita, representada por um pool de conexões pequeno e por um custo de
20 ms por gravação (pg_sleep). Com 10 conexões, a capacidade é de cerca de 500 gravações por segundo.
"""
import os
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI, HTTPException
from psycopg_pool import AsyncConnectionPool, PoolTimeout
from pydantic import BaseModel

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://luna:luna@postgres:5432/confirmacoes")
AMQP_URL = os.environ.get("AMQP_URL", "amqp://guest:guest@rabbitmq/")
POOL_MAX = int(os.environ.get("POOL_MAX", "10"))
ESPERA_POOL_S = float(os.environ.get("ESPERA_POOL_S", "1.0"))

SQL_GRAVAR = (
    "INSERT INTO confirmacoes (codigo, recebida_em, processada_em) VALUES (%s, now(), now()) "
    "ON CONFLICT (codigo) DO NOTHING"
)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    app.state.pool = AsyncConnectionPool(DATABASE_URL, min_size=1, max_size=POOL_MAX, open=False)
    await app.state.pool.open()
    app.state.amqp = await aio_pika.connect_robust(AMQP_URL)
    app.state.canal = await app.state.amqp.channel()          # com confirmação de publicação
    await app.state.canal.declare_queue("confirmacoes", durable=True)
    yield
    await app.state.amqp.close()
    await app.state.pool.close()


app = FastAPI(title="LunaLog: confirmacoes", lifespan=ciclo_de_vida)


class Confirmacao(BaseModel):
    codigo: str


@app.post("/confirmacoes/direto", status_code=201)
async def direto(c: Confirmacao):
    try:
        async with app.state.pool.connection(timeout=ESPERA_POOL_S) as conn:
            await conn.execute("SELECT pg_sleep(0.02)")       # custo de trabalho do banco
            await conn.execute(SQL_GRAVAR, (c.codigo,))
    except PoolTimeout:
        raise HTTPException(503, "banco saturado: sem conexao livre")
    return {"codigo": c.codigo, "estado": "gravada"}


@app.post("/confirmacoes/fila", status_code=202)
async def fila(c: Confirmacao):
    mensagem = aio_pika.Message(body=c.codigo.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
    await app.state.canal.default_exchange.publish(mensagem, routing_key="confirmacoes")
    return {"codigo": c.codigo, "estado": "aceita"}


@app.get("/estado")
async def estado():
    async with app.state.pool.connection() as conn:
        gravadas = (await (await conn.execute("SELECT count(*) FROM confirmacoes")).fetchone())[0]
    return {"gravadas": gravadas}


@app.post("/admin/limpar")
async def limpar():
    async with app.state.pool.connection() as conn:
        await conn.execute("TRUNCATE confirmacoes")
    for nome in ("confirmacoes", "confirmacoes.retry", "confirmacoes.dlq"):
        canal = await app.state.amqp.channel()   # um canal por fila: declarar uma fila inexistente fecha o canal
        try:
            fila_ = await canal.declare_queue(nome, passive=True)
            await fila_.purge()
        except Exception:
            pass                                 # a fila ainda nao existe: tudo bem
    return {"ok": True}
