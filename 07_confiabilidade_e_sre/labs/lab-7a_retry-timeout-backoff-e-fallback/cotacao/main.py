"""Serviço de cotação da LunaLog (lab 7A): a política de retry é escolhida em tempo de execução.

  sem-retry       : 1 tentativa, timeout de 1 s
  retry-imediato  : até 4 tentativas, uma logo após a outra
  backoff-jitter  : até 4 tentativas, com espera exponencial aleatória (full jitter) entre elas
  completo        : backoff com jitter + orçamento de retries (10%) + fallback quando tudo falha

Em todas as políticas com retry, há um prazo total (deadline) de 3 s por requisição.
"""
import asyncio
import os
import random
import time
from collections import defaultdict

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

URL_MAPAS = os.environ["URL_MAPAS"]
POLITICAS = ("sem-retry", "retry-imediato", "backoff-jitter", "completo")
TENTATIVAS_MAX = 4
PRAZO_TOTAL = 3.0
TIMEOUT_TENTATIVA = 1.0
BASE_BACKOFF = 0.1
TETO_BACKOFF = 2.0

config = {"politica": "sem-retry"}
orcamento = {"fichas": 10.0}  # orçamento de retries: cada requisição ganha 0,1 ficha; cada retry custa 1
por_segundo = defaultdict(lambda: {"ok": 0, "fallback": 0, "erro": 0, "tentativas": 0})
cliente = httpx.AsyncClient(timeout=TIMEOUT_TENTATIVA, limits=httpx.Limits(max_connections=500))

app = FastAPI(title="Cotação")


def registrar(chave: str, n: int = 1):
    por_segundo[int(time.time())][chave] += n


async def tentar() -> bool:
    registrar("tentativas")
    try:
        r = await cliente.get(f"{URL_MAPAS}/rota")
        return r.status_code == 200
    except httpx.HTTPError:
        return False


def pode_tentar_de_novo(politica: str) -> bool:
    if politica != "completo":
        return True
    if orcamento["fichas"] >= 1:
        orcamento["fichas"] -= 1
        return True
    return False


@app.get("/cotacao/{entrega_id}")
async def cotacao(entrega_id: str):
    politica = config["politica"]
    orcamento["fichas"] = min(10.0, orcamento["fichas"] + 0.1)
    inicio = time.time()
    maximo = 1 if politica == "sem-retry" else TENTATIVAS_MAX

    for n in range(maximo):
        if n > 0:
            if time.time() - inicio >= PRAZO_TOTAL or not pode_tentar_de_novo(politica):
                break
            if politica in ("backoff-jitter", "completo"):
                # full jitter: espera aleatória entre 0 e o teto exponencial, para os clientes não retentarem em bloco
                await asyncio.sleep(random.uniform(0, min(TETO_BACKOFF, BASE_BACKOFF * 2 ** (n - 1))))
        if await tentar():
            registrar("ok")
            return {"entrega": entrega_id, "frete": 46.25, "fonte": "mapas"}

    if politica == "completo":
        registrar("fallback")
        return {"entrega": entrega_id, "frete": 46.0, "fonte": "estimativa (fallback)"}
    registrar("erro")
    raise HTTPException(503, "mapas indisponivel")


@app.post("/config")
async def configurar(politica: str):
    if politica not in POLITICAS:
        raise HTTPException(400, f"politica invalida; use uma de {POLITICAS}")
    config["politica"] = politica
    orcamento["fichas"] = 10.0
    por_segundo.clear()
    return {"politica": politica}


@app.get("/resultados/grafico", response_class=PlainTextResponse)
async def grafico():
    """O que o cliente da cotação viu, por segundo: sucessos, fallbacks, erros e tentativas feitas à API de mapas."""
    if not por_segundo:
        return "sem dados\n"
    ini, fim = min(por_segundo), max(por_segundo)
    linhas = [f"Cotação (política: {config['politica']}): ok / fallback / erro por segundo, e tentativas feitas aos mapas"]
    tot = defaultdict(int)
    for s in range(ini, fim + 1):
        d = por_segundo.get(s, {"ok": 0, "fallback": 0, "erro": 0, "tentativas": 0})
        for k, v in d.items():
            tot[k] += v
        linhas.append(f"t+{s - ini:>3}s ok={d['ok']:>3} fb={d['fallback']:>3} erro={d['erro']:>3} tent={d['tentativas']:>4} {'x' * min(d['erro'] // 2, 40)}")
    reqs = tot["ok"] + tot["fallback"] + tot["erro"]
    linhas.append(f"total: {reqs} requisições, {tot['ok']} ok, {tot['fallback']} fallback, {tot['erro']} erro; "
                  f"{tot['tentativas']} tentativas ({tot['tentativas'] / max(reqs, 1):.2f} por requisição)")
    return "\n".join(linhas) + "\n"
