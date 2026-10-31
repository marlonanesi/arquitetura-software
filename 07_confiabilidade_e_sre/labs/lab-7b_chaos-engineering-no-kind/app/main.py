"""Serviço de frete e sua dependência (lab 7B: chaos engineering).

A mesma imagem faz dois papéis, escolhidos por variável de ambiente:

  PAPEL=transportadora  responde a cotação "oficial" (a dependência externa)
  PAPEL=frete           consulta a transportadora e devolve a cotação ao cliente

O serviço de frete roda em duas versões de configuração:
  - frágil:    espera a dependência até TIMEOUT_S segundos (longo) e não tem alternativa
  - protegido: timeout curto e FALLBACK=sim (devolve uma tabela local, "degradada", em vez de falhar)

O código é o mesmo; a diferença é só de configuração. É isso que o experimento de caos vai comparar.
"""
import os
import socket

import httpx
from fastapi import FastAPI, HTTPException, Response

PAPEL = os.environ.get("PAPEL", "frete")
URL_DEP = os.environ.get("URL_DEP", "http://transportadora:8000")
TIMEOUT_S = float(os.environ.get("TIMEOUT_S", "5"))
FALLBACK = os.environ.get("FALLBACK", "nao").lower() in ("sim", "true", "1")
POD = socket.gethostname()

app = FastAPI(title=f"Frete ({PAPEL})")


@app.get("/saude")
async def saude():
    return {"status": "ok", "papel": PAPEL, "pod": POD}


@app.get("/cotacao")
async def cotacao(response: Response):
    if PAPEL == "transportadora":
        response.headers["X-Origem"] = "transportadora"
        return {"valor": 42.90, "prazo_dias": 3, "pod": POD}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as cliente:
            r = await cliente.get(f"{URL_DEP}/cotacao")
            r.raise_for_status()
        response.headers["X-Origem"] = "transportadora"
        return {"valor": r.json()["valor"], "origem": "transportadora", "pod": POD}
    except (httpx.HTTPError, OSError):
        if FALLBACK:
            # Resposta degradada, mas útil: uma tabela local com o valor médio.
            response.headers["X-Origem"] = "tabela-local"
            return {"valor": 45.00, "origem": "tabela-local", "pod": POD}
        raise HTTPException(502, "transportadora indisponivel")
