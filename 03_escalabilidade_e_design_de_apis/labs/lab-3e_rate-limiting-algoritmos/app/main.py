"""Três algoritmos de rate limiting lado a lado, com estado no Redis (lab 3E).

  GET /fixa         janela fixa:      no máximo LIMITE requisições por janela de JANELA_S segundos
  GET /deslizante   janela deslizante: no máximo LIMITE nos últimos JANELA_S segundos (a qualquer instante)
  GET /bucket       token bucket:     rajada de até LIMITE, reposição média de LIMITE/JANELA_S por segundo

  ?escopo=cliente   (padrão) um contador por chave de API (header X-Api-Key)
  ?escopo=global    um contador único para todos os clientes
  ?armazenamento=memoria   (só /fixa) contador na memória da réplica, em vez do Redis

As decisões do Redis são feitas por scripts Lua, que executam de forma atômica: duas réplicas nunca
leem o mesmo valor "velho" ao mesmo tempo.
"""
import os
import socket
import time
import uuid

import redis.asyncio as redis
from fastapi import FastAPI, Header, Request, Response
from fastapi.responses import JSONResponse

LIMITE = int(os.environ.get("LIMITE", "10"))
JANELA_S = float(os.environ.get("JANELA_S", "5"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="LunaLog: rate limiting")
r = redis.from_url(REDIS_URL, decode_responses=True)
memoria: dict[str, int] = {}

# Janela fixa: um contador por janela. INCR e a expiração acontecem juntos.
LUA_FIXA = """
local c = redis.call('INCR', KEYS[1])
if c == 1 then redis.call('PEXPIRE', KEYS[1], ARGV[1]) end
return c
"""

# Janela deslizante (log): guarda o instante de cada requisição aceita e conta as dos últimos W ms.
LUA_DESLIZANTE = """
local t = redis.call('TIME')
local agora = t[1] * 1000 + math.floor(t[2] / 1000)
local janela = tonumber(ARGV[1])
local limite = tonumber(ARGV[2])
redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, agora - janela)
local n = redis.call('ZCARD', KEYS[1])
if n < limite then
  redis.call('ZADD', KEYS[1], agora, ARGV[3])
  redis.call('PEXPIRE', KEYS[1], janela)
  return {1, limite - n - 1, 0}
end
local mais_antiga = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
return {0, 0, tonumber(mais_antiga[2]) + janela - agora}
"""

# Token bucket: um balde com capacidade C que se enche a R fichas por ms; cada requisição gasta uma ficha.
LUA_BUCKET = """
local t = redis.call('TIME')
local agora = t[1] * 1000 + math.floor(t[2] / 1000)
local capacidade = tonumber(ARGV[1])
local taxa = tonumber(ARGV[2])
local d = redis.call('HMGET', KEYS[1], 'fichas', 'ts')
local fichas = tonumber(d[1]) or capacidade
local ts = tonumber(d[2]) or agora
fichas = math.min(capacidade, fichas + (agora - ts) * taxa)
local ok = 0
if fichas >= 1 then fichas = fichas - 1; ok = 1 end
redis.call('HSET', KEYS[1], 'fichas', fichas, 'ts', agora)
redis.call('PEXPIRE', KEYS[1], math.ceil(capacidade / taxa) * 2)
local espera = 0
if ok == 0 then espera = math.ceil((1 - fichas) / taxa) end
return {ok, math.floor(fichas), espera}
"""


async def decidir(algoritmo: str, chave: str, armazenamento: str):
    """Devolve (permitido, restantes, espera_em_ms)."""
    agora = time.time()
    janela_ms = int(JANELA_S * 1000)
    if algoritmo == "fixa":
        id_janela = int(agora // JANELA_S)
        espera_ms = int(((id_janela + 1) * JANELA_S - agora) * 1000)
        k = f"rl:fixa:{chave}:{id_janela}"
        if armazenamento == "memoria":
            memoria[k] = memoria.get(k, 0) + 1
            c = memoria[k]
        else:
            c = int(await r.eval(LUA_FIXA, 1, k, janela_ms * 2))
        return c <= LIMITE, max(LIMITE - c, 0), espera_ms
    if algoritmo == "deslizante":
        ok, restantes, espera = await r.eval(LUA_DESLIZANTE, 1, f"rl:desl:{chave}", janela_ms, LIMITE, uuid.uuid4().hex)
        return bool(ok), int(restantes), int(espera)
    taxa_por_ms = LIMITE / janela_ms
    ok, restantes, espera = await r.eval(LUA_BUCKET, 1, f"rl:bucket:{chave}", LIMITE, taxa_por_ms)
    return bool(ok), int(restantes), int(espera)


async def limitar(algoritmo: str, request: Request, response: Response, chave_api: str, escopo: str, armazenamento: str):
    chave = "global" if escopo == "global" else (chave_api or "anonimo")
    permitido, restantes, espera_ms = await decidir(algoritmo, chave, armazenamento)
    cabecalhos = {
        "X-RateLimit-Limit": str(LIMITE),
        "X-RateLimit-Remaining": str(restantes),
        "X-Replica": REPLICA,
    }
    if not permitido:
        cabecalhos["Retry-After"] = str(max(1, round(espera_ms / 1000)))
        return JSONResponse({"erro": "limite excedido", "tente_novamente_em_ms": espera_ms}, status_code=429, headers=cabecalhos)
    return JSONResponse({"ok": True, "chave": chave, "replica": REPLICA}, headers=cabecalhos)


@app.get("/fixa")
async def fixa(request: Request, response: Response, x_api_key: str = Header(default=""), escopo: str = "cliente", armazenamento: str = "redis"):
    return await limitar("fixa", request, response, x_api_key, escopo, armazenamento)


@app.get("/deslizante")
async def deslizante(request: Request, response: Response, x_api_key: str = Header(default=""), escopo: str = "cliente"):
    return await limitar("deslizante", request, response, x_api_key, escopo, "redis")


@app.get("/bucket")
async def bucket(request: Request, response: Response, x_api_key: str = Header(default=""), escopo: str = "cliente"):
    return await limitar("bucket", request, response, x_api_key, escopo, "redis")


@app.get("/config")
async def config():
    return {"limite": LIMITE, "janela_s": JANELA_S, "replica": REPLICA, "hora": time.time()}
