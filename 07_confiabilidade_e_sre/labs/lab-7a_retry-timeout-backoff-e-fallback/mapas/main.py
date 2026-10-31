"""API de mapas simulada, com um modelo simples de congestionamento.

Duas razões para ela recusar chamadas (HTTP 503):
  1. uma falha injetada (POST /falha?segundos=N), que representa a causa original do incidente;
  2. congestionamento: se chegarem mais de LIMITE_CONGESTAO chamadas em 1 segundo, ela engasga
     e recusa TUDO pelos próximos 5 segundos.

O congestionamento é o que mostra o perigo do retry: quando os clientes insistem, a própria
insistência mantém a API congestionada, mesmo depois de a causa original ter acabado.
(Modelo simplificado, de propósito: em sistemas reais o efeito aparece como filas, pools
esgotados e caches frios, mas a dinâmica é a mesma.)
"""
import asyncio
import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

LIMITE = int(os.environ.get("LIMITE_CONGESTAO", "80"))
LATENCIA = 0.04

app = FastAPI(title="Mapas")
estado = {"falha_ate": 0.0, "congestionado_ate": 0.0, "inicio": None}
chegadas = deque()
por_segundo = defaultdict(lambda: {"recebidas": 0, "atendidas": 0})


@app.get("/rota")
async def rota():
    agora = time.time()
    if estado["inicio"] is None:
        estado["inicio"] = int(agora)
    chegadas.append(agora)
    while chegadas and chegadas[0] < agora - 1:
        chegadas.popleft()
    segundo = int(agora)
    por_segundo[segundo]["recebidas"] += 1

    if len(chegadas) > LIMITE:
        estado["congestionado_ate"] = agora + 5

    if agora < estado["falha_ate"] or agora < estado["congestionado_ate"]:
        raise HTTPException(503, "indisponivel")

    await asyncio.sleep(LATENCIA)
    por_segundo[segundo]["atendidas"] += 1
    return {"distancia_km": 42.5}


@app.post("/falha")
async def falha(segundos: int = 8):
    estado["falha_ate"] = time.time() + segundos
    return {"falha_por_segundos": segundos}


@app.post("/reiniciar")
async def reiniciar():
    estado.update(falha_ate=0.0, congestionado_ate=0.0, inicio=None)
    chegadas.clear()
    por_segundo.clear()
    return {"ok": True}


@app.get("/estatisticas/grafico", response_class=PlainTextResponse)
async def grafico():
    """Chamadas recebidas e atendidas pela API de mapas, por segundo."""
    if not por_segundo:
        return "sem dados\n"
    ini, fim = min(por_segundo), max(por_segundo)
    linhas = [f"API de mapas: recebidas / atendidas por segundo (limite de congestionamento: {LIMITE})"]
    total_rec = total_ok = 0
    for s in range(ini, fim + 1):
        d = por_segundo.get(s, {"recebidas": 0, "atendidas": 0})
        total_rec += d["recebidas"]
        total_ok += d["atendidas"]
        marca = "!" if d["recebidas"] > LIMITE else " "
        linhas.append(f"t+{s - ini:>3}s {d['recebidas']:>4} / {d['atendidas']:>4} {marca} {'#' * min(d['recebidas'] // 3, 60)}")
    linhas.append(f"total: {total_rec} recebidas, {total_ok} atendidas")
    return "\n".join(linhas) + "\n"
