"""API de cotação da LunaLog para o lab 3A (escala horizontal).

  GET  /cotacao          consome CPU de verdade (cerca de 25 ms), para o HPA ter o que medir
  GET  /consulta         depende de um "banco" de capacidade fixa, para mostrar o limite do scale-out
  POST /sessao/entrar    cria uma sessão (guardada em memória ou no Redis, conforme SESSOES)
  GET  /sessao/perfil    lê a sessão
  GET  /info             qual pod respondeu
"""
import hashlib
import os
import socket
import time
import urllib.request
import uuid

import redis
from fastapi import FastAPI, HTTPException, Response

POD = socket.gethostname()
SESSOES = os.environ.get("SESSOES", "memoria")  # memoria | redis
BANCO_URL = os.environ.get("BANCO_URL", "http://banco:8000/")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CUSTO_CPU_MS = int(os.environ.get("CUSTO_CPU_MS", "25"))

app = FastAPI(title="Cotação (lab 3A)")
sessoes_em_memoria: dict[str, str] = {}
cache_redis = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1, socket_timeout=1)


@app.get("/info")
def info(response: Response):
    response.headers["X-Pod"] = POD
    return {"pod": POD, "sessoes": SESSOES}


@app.get("/cotacao")
def cotacao(response: Response):
    # Trabalho de CPU: representa o cálculo de uma cotação de frete.
    fim = time.perf_counter() + CUSTO_CPU_MS / 1000
    while time.perf_counter() < fim:
        hashlib.sha256(b"x" * 2000).digest()
    response.headers["X-Pod"] = POD
    return {"frete": 46.25, "pod": POD}


@app.get("/consulta")
def consulta(response: Response):
    try:
        with urllib.request.urlopen(BANCO_URL, timeout=10) as r:
            r.read()
    except Exception:  # noqa: BLE001
        raise HTTPException(503, "banco indisponivel")
    response.headers["X-Pod"] = POD
    return {"ok": True, "pod": POD}


@app.post("/sessao/entrar")
def entrar(usuario: str, response: Response):
    sid = uuid.uuid4().hex[:12]
    if SESSOES == "redis":
        cache_redis.set(f"sessao:{sid}", usuario, ex=1800)
    else:
        sessoes_em_memoria[sid] = usuario
    response.headers["X-Pod"] = POD
    return {"sid": sid, "pod": POD, "sessoes": SESSOES}


@app.get("/sessao/perfil")
def perfil(sid: str, response: Response):
    response.headers["X-Pod"] = POD
    if SESSOES == "redis":
        valor = cache_redis.get(f"sessao:{sid}")
        usuario = valor.decode() if valor else None
    else:
        usuario = sessoes_em_memoria.get(sid)
    if usuario is None:
        raise HTTPException(401, f"sessao nao encontrada no pod {POD}")
    return {"usuario": usuario, "pod": POD}
