"""Serviço de tracking versionado, para os labs de estratégias de deploy (5C e 5D).

A mesma imagem pode ser construída em várias versões. A variável QUEBRADA=1 simula uma versão
com defeito: ela sobe, mas nunca fica saudável (ou, no modo ERRO_PCT, falha em parte das requisições).
"""
import os
import socket
import time

from fastapi import FastAPI, HTTPException, Response

VERSAO = os.environ.get("VERSAO", "dev")
QUEBRADA = os.environ.get("QUEBRADA", "0") == "1"
ERRO_PCT = float(os.environ.get("ERRO_PCT", "0"))
AQUECIMENTO = float(os.environ.get("AQUECIMENTO", "5"))
POD = socket.gethostname()
inicio = time.time()

app = FastAPI(title="Tracking versionado")


@app.get("/")
def raiz(response: Response):
    import random
    if ERRO_PCT and random.random() * 100 < ERRO_PCT:
        raise HTTPException(500, f"defeito simulado na versao {VERSAO}")
    response.headers["X-Versao"] = VERSAO
    return {"versao": VERSAO, "pod": POD}


@app.get("/saude")
def saude():
    # Pronto só depois do aquecimento e se a versão não for a "quebrada".
    if QUEBRADA or time.time() - inicio < AQUECIMENTO:
        raise HTTPException(503, "nao esta pronto")
    return {"status": "ok", "versao": VERSAO}
