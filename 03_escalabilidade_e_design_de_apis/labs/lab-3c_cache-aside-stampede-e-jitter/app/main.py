"""Serviço de tarifas de frete da LunaLog (lab 3C).

A estratégia de cache é escolhida por requisição (?estrategia=...), para comparar
os comportamentos sem trocar de versão:

  sem-cache   : toda requisição vai ao banco
  ttl-fixo    : cache-aside com TTL fixo
  ttl-jitter  : cache-aside com TTL aleatório (varia em torno do TTL)
  jitter-lock : jitter + lock de regeneração (só uma requisição reconstrói a chave)
"""
import os
import random
import threading
import time
from contextlib import asynccontextmanager

import anyio.to_thread
import redis
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import PlainTextResponse
from psycopg_pool import ConnectionPool, PoolTimeout

DATABASE_URL = os.environ["DATABASE_URL"]
REDIS_URL = os.environ["REDIS_URL"]
TTL = float(os.environ.get("TTL_SEGUNDOS", "10"))
DB_LATENCIA = float(os.environ.get("DB_LATENCIA_SEGUNDOS", "0.15"))
POOL_MAX = int(os.environ.get("DB_POOL_MAX", "10"))
ESTRATEGIAS = ("sem-cache", "ttl-fixo", "ttl-jitter", "jitter-lock")

cache = redis.Redis.from_url(REDIS_URL)
pool = ConnectionPool(DATABASE_URL, min_size=2, max_size=POOL_MAX, timeout=2.0,
                      kwargs={"autocommit": True}, open=False)

trava = threading.Lock()
consultas_por_segundo: dict[int, int] = {}
contadores = {"banco": 0, "hits": 0, "misses": 0}


@asynccontextmanager
async def ciclo_de_vida(_app):
    # Muitas requisições ficam esperando o banco; o pool de threads padrão (40) viraria o gargalo.
    anyio.to_thread.current_default_thread_limiter().total_tokens = 400
    pool.open()
    yield
    pool.close()


app = FastAPI(title="Tarifas LunaLog", lifespan=ciclo_de_vida)


def consultar_banco(rota: str) -> float:
    with pool.connection() as conn:
        # pg_sleep simula uma consulta cara (junções, cálculo de tarifa)
        linha = conn.execute(
            "SELECT t.valor FROM tarifas t, pg_sleep(%s) WHERE t.rota = %s", (DB_LATENCIA, rota)
        ).fetchone()
    with trava:
        contadores["banco"] += 1
        segundo = int(time.time())
        consultas_por_segundo[segundo] = consultas_por_segundo.get(segundo, 0) + 1
    if linha is None:
        raise KeyError(rota)
    return float(linha[0])


def ttl_para(estrategia: str) -> float:
    if estrategia == "ttl-fixo":
        return TTL
    return TTL * random.uniform(0.5, 1.5)  # jitter: cada chave expira num momento diferente


def gravar_cache(rota: str, valor: float, estrategia: str):
    cache.set(f"tarifa:{rota}", str(valor), px=int(ttl_para(estrategia) * 1000))


def ler_tarifa(rota: str, estrategia: str) -> tuple[float, str]:
    if estrategia == "sem-cache":
        return consultar_banco(rota), "banco"

    bruto = cache.get(f"tarifa:{rota}")
    if bruto is not None:
        with trava:
            contadores["hits"] += 1
        return float(bruto), "cache"
    with trava:
        contadores["misses"] += 1

    if estrategia != "jitter-lock":
        valor = consultar_banco(rota)
        gravar_cache(rota, valor, estrategia)
        return valor, "banco"

    # jitter-lock: só uma requisição reconstrói a chave; as outras esperam o resultado dela.
    if cache.set(f"lock:{rota}", "1", nx=True, px=3000):
        try:
            valor = consultar_banco(rota)
            gravar_cache(rota, valor, estrategia)
            return valor, "banco"
        finally:
            cache.delete(f"lock:{rota}")
    limite = time.time() + 2.0
    while time.time() < limite:
        time.sleep(0.02)
        bruto = cache.get(f"tarifa:{rota}")
        if bruto is not None:
            return float(bruto), "cache (esperou o lock)"
    return consultar_banco(rota), "banco (lock expirou)"


@app.get("/tarifa/{rota}")
def tarifa(rota: str, response: Response, estrategia: str = "ttl-fixo"):
    if estrategia not in ESTRATEGIAS:
        raise HTTPException(400, f"estrategia invalida; use uma de {ESTRATEGIAS}")
    try:
        valor, origem = ler_tarifa(rota, estrategia)
    except KeyError:
        raise HTTPException(404, "rota nao encontrada")
    except PoolTimeout:
        raise HTTPException(503, "banco saturado")
    response.headers["X-Origem"] = origem
    return {"rota": rota, "valor": valor, "origem": origem}


@app.post("/admin/reiniciar")
def reiniciar(estrategia: str = "ttl-fixo", aquecer: bool = False):
    """Limpa cache e contadores. Com aquecer=true, pré-carrega as 200 rotas de uma vez
    (o que sincroniza a expiração quando o TTL é fixo)."""
    cache.flushdb()
    with trava:
        consultas_por_segundo.clear()
        contadores.update(banco=0, hits=0, misses=0)
    if aquecer and estrategia != "sem-cache":
        # Carga em lote, como um job de aquecimento: todas as chaves nascem no mesmo instante.
        with pool.connection() as conn:
            linhas = conn.execute("SELECT rota, valor FROM tarifas").fetchall()
        for rota, valor in linhas:
            gravar_cache(rota, float(valor), estrategia)
    return {"ok": True, "estrategia": estrategia, "aquecido": aquecer}


@app.get("/stats")
def stats():
    with trava:
        serie = dict(consultas_por_segundo)
        resumo = dict(contadores)
    pico = max(serie.values(), default=0)
    return {**resumo, "pico_consultas_por_segundo": pico}


@app.get("/stats/grafico", response_class=PlainTextResponse)
def grafico(segundos: int = 60):
    """Consultas ao banco por segundo, em texto, para ver o pico sem precisar de Grafana."""
    with trava:
        serie = dict(consultas_por_segundo)
        resumo = dict(contadores)
    if not serie:
        return "sem consultas ao banco registradas\n"
    fim = max(serie)
    inicio = max(min(serie), fim - segundos + 1)
    linhas = [f"Consultas ao banco por segundo (total={resumo['banco']}, hits={resumo['hits']}, misses={resumo['misses']})"]
    for s in range(inicio, fim + 1):
        n = serie.get(s, 0)
        linhas.append(f"t+{s - inicio:>3}s {n:>4} {'#' * min(n // 2, 70)}")
    linhas.append(f"pico: {max(serie.values())} consultas em 1 segundo")
    return "\n".join(linhas) + "\n"
