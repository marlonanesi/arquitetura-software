"""Serviço de comprovantes de entrega da LunaLog (versão do lab 2C).

O comportamento muda por configuração, não por código: a mesma imagem roda
com armazenamento local (estado preso ao contêiner) ou externalizado (Redis).
"""
import os
import socket
import time
import uuid
from pathlib import Path

import redis
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

VERSAO = os.environ.get("VERSAO", "dev")
ARMAZENAMENTO = os.environ.get("ARMAZENAMENTO", "local")  # local | redis
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
WARMUP_SEGUNDOS = int(os.environ.get("WARMUP_SEGUNDOS", "20"))
BANNER = os.environ.get("BANNER", "")
TOKEN_INTEGRACAO = os.environ.get("TOKEN_INTEGRACAO", "")
POD = socket.gethostname()
PASTA_LOCAL = Path("/tmp/comprovantes")

app = FastAPI(title="Comprovantes LunaLog", version=VERSAO)

inicio = time.time()
estado = {"travado": False}
cliente_redis = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=1, socket_timeout=1) if ARMAZENAMENTO == "redis" else None
PASTA_LOCAL.mkdir(parents=True, exist_ok=True)


class Comprovante(BaseModel):
    entrega_id: str
    conteudo: str


def aquecido() -> bool:
    return time.time() - inicio >= WARMUP_SEGUNDOS


def redis_ok() -> bool:
    if cliente_redis is None:
        return True
    try:
        return bool(cliente_redis.ping())
    except redis.RedisError:
        return False


def exigir_pronto():
    # Antes do aquecimento (ex.: carga de cache) a aplicação ainda não atende de verdade.
    if not aquecido():
        raise HTTPException(status_code=503, detail="aquecendo")


@app.get("/")
def raiz(response: Response):
    response.headers["X-Pod"] = POD
    return {
        "servico": "comprovantes",
        "versao": VERSAO,
        "pod": POD,
        "armazenamento": ARMAZENAMENTO,
        "banner": BANNER,
        "token_integracao_configurado": bool(TOKEN_INTEGRACAO),
    }


@app.post("/comprovantes", status_code=201)
def criar(c: Comprovante, response: Response):
    exigir_pronto()
    cid = uuid.uuid4().hex[:8]
    if ARMAZENAMENTO == "redis":
        cliente_redis.set(f"comprovante:{cid}", c.conteudo)
    else:
        (PASTA_LOCAL / cid).write_text(c.conteudo)
    response.headers["X-Pod"] = POD
    return {"id": cid, "entrega_id": c.entrega_id, "salvo_em": POD if ARMAZENAMENTO == "local" else "redis"}


@app.get("/comprovantes/{cid}")
def ler(cid: str, response: Response):
    exigir_pronto()
    response.headers["X-Pod"] = POD
    if ARMAZENAMENTO == "redis":
        valor = cliente_redis.get(f"comprovante:{cid}")
        conteudo = valor.decode() if valor is not None else None
    else:
        arquivo = PASTA_LOCAL / cid
        conteudo = arquivo.read_text() if arquivo.exists() else None
    if conteudo is None:
        raise HTTPException(status_code=404, detail=f"comprovante nao encontrado no pod {POD}")
    return {"id": cid, "conteudo": conteudo, "lido_em": POD}


# --- health checks: contratos entre a aplicação e a plataforma ---------------------------

@app.get("/health/live")
def live():
    """Liveness: o processo está saudável o bastante para continuar vivo? Se não, reinicie."""
    if estado["travado"]:
        raise HTTPException(status_code=500, detail="travado")
    return {"status": "vivo", "pod": POD}


@app.get("/health/ready")
def ready():
    """Readiness: posso receber tráfego agora? Se não, tire-me do balanceamento (sem reiniciar)."""
    if not aquecido():
        raise HTTPException(status_code=503, detail="aquecendo")
    if not redis_ok():
        raise HTTPException(status_code=503, detail="redis indisponivel")
    return {"status": "pronto", "pod": POD}


@app.post("/admin/travar")
def travar():
    """Simula um deadlock: a aplicação deixa de responder bem no liveness."""
    estado["travado"] = True
    return {"pod": POD, "travado": True}
