"""Fluxo de cotação da LunaLog: quatro serviços encadeados, uma única imagem.

  cotacao -> rotas -> tarifas -> transportadoras

O papel de cada contêiner vem da variável SERVICO.
"""
import asyncio
import logging
import os

import httpx
from fastapi import FastAPI
from opentelemetry import trace

import telemetria

SERVICO = os.environ["SERVICO"]
URL_PROXIMO = os.environ.get("URL_PROXIMO", "")
VIASUL_MS = int(os.environ.get("VIASUL_MS", "2800"))
PROPAGAR = os.environ.get("PROPAGAR_CONTEXTO", "1") == "1"

app = FastAPI(title=f"LunaLog {SERVICO}")
telemetria.configurar(app, propagar_contexto=PROPAGAR)
tracer = trace.get_tracer(SERVICO)
log = logging.getLogger(SERVICO)

# Transportadoras consultadas, em sequência: nome e tempo de resposta (ms)
TRANSPORTADORAS = [("TransRapida", 90), ("LogMax", 140), ("ViaSul", VIASUL_MS)]


async def chamar_proximo(caminho: str, **params):
    async with httpx.AsyncClient(timeout=15) as cliente:
        r = await cliente.get(f"{URL_PROXIMO}{caminho}", params=params)
        r.raise_for_status()
        return r.json()


@app.get("/cotacao")
async def cotacao(destino: str = "SP"):
    contexto = trace.get_current_span().get_span_context()
    log.info(f"cotação recebida para {destino}")
    resultado = await chamar_proximo("/rota", destino=destino)
    log.info("cotação concluída")
    return {"destino": destino, "frete": resultado["frete"], "melhor": resultado["melhor"],
            "trace_id": format(contexto.trace_id, "032x")}


@app.get("/rota")
async def rota(destino: str):
    log.info(f"calculando rota até {destino}")
    await asyncio.sleep(0.03)
    return await chamar_proximo("/tarifa", km=420, destino=destino)


@app.get("/tarifa")
async def tarifa(km: int, destino: str):
    # Span manual: o instrumentador automático não conhece a regra de negócio.
    with tracer.start_as_current_span("calcular_tarifa") as span:
        span.set_attribute("tarifa.destino", destino)
        span.set_attribute("tarifa.km", km)
        log.info(f"calculando tarifa para {km} km")
        await asyncio.sleep(0.02)
        ofertas = await chamar_proximo("/cotar", peso_kg=12)
        span.set_attribute("tarifa.ofertas", len(ofertas["ofertas"]))
    return {"frete": ofertas["menor_preco"], "melhor": ofertas["melhor"]}


@app.get("/cotar")
async def cotar(peso_kg: int):
    ofertas = []
    for nome, ms in TRANSPORTADORAS:
        with tracer.start_as_current_span("consultar_transportadora") as span:
            span.set_attribute("transportadora.nome", nome)
            log.info(f"consultando {nome}")
            await asyncio.sleep(ms / 1000)
            preco = round(20 + ms / 100, 2)
            span.set_attribute("transportadora.preco", preco)
            ofertas.append({"transportadora": nome, "preco": preco})
    melhor = min(ofertas, key=lambda o: o["preco"])
    return {"ofertas": ofertas, "menor_preco": melhor["preco"], "melhor": melhor["transportadora"]}
