"""Serviço de tracking versionado, com métricas no formato Prometheus (lab 5D).

A mesma imagem em várias versões. A variável ERRO_PCT simula uma versão com defeito:
ela passa na readiness (sobe e fica "saudável"), mas falha em parte das requisições reais.
É o tipo de defeito que a readiness NÃO pega e que a análise de métricas do canary pega.
"""
import os
import random
import socket
import threading
import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse

VERSAO = os.environ.get("VERSAO", "dev")
ERRO_PCT = float(os.environ.get("ERRO_PCT", "0"))
POD = socket.gethostname()

app = FastAPI(title="Tracking versionado com metricas")
trava = threading.Lock()
contagem: dict[str, int] = {}


@app.middleware("http")
async def contar(request: Request, call_next):
    resposta = None
    try:
        resposta = await call_next(request)
        return resposta
    finally:
        if request.url.path == "/":
            status = str(resposta.status_code) if resposta is not None else "500"
            with trava:
                contagem[status] = contagem.get(status, 0) + 1


@app.get("/")
def raiz(response: Response):
    if ERRO_PCT and random.random() * 100 < ERRO_PCT:
        raise HTTPException(500, f"defeito simulado na versao {VERSAO}")
    response.headers["X-Versao"] = VERSAO
    return {"versao": VERSAO, "pod": POD}


@app.get("/saude")
def saude():
    return {"status": "ok", "versao": VERSAO}


@app.get("/metrics", response_class=PlainTextResponse)
def metricas():
    linhas = ["# HELP http_requests_total Requisicoes recebidas em /", "# TYPE http_requests_total counter"]
    with trava:
        for status, n in sorted(contagem.items()):
            linhas.append(f'http_requests_total{{versao="{VERSAO}",status="{status}"}} {n}')
    return "\n".join(linhas) + "\n"
