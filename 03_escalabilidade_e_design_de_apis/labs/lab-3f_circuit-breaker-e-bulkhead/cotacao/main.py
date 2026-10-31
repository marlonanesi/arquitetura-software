"""Serviço de cotação da LunaLog (lab 3F).

Depende de duas coisas externas: a API de mapas (calcula a rota) e o serviço de
notificação. A proteção contra falha dessas dependências é escolhida em tempo de
execução (POST /config?protecao=...), para comparar sem trocar de versão:

  nenhuma   : timeout de 30 s, sem circuit breaker, sem bulkhead
  breaker   : timeout de 1 s + circuit breaker em cada dependência
  bulkhead  : timeout de 3 s + limite de chamadas simultâneas por dependência
  completo  : timeout de 1 s + circuit breaker + bulkhead
"""
import os
import threading
import time
from collections import deque
from contextlib import asynccontextmanager

import anyio.to_thread
import httpx
from fastapi import FastAPI, HTTPException, Response

URL_MAPAS = os.environ["URL_MAPAS"]
URL_NOTIFICACAO = os.environ["URL_NOTIFICACAO"]
THREADS = int(os.environ.get("THREADS", "30"))

PROTECOES = {
    #            timeout  breaker  bulkhead
    "nenhuma":  (30.0,    False,   False),
    "breaker":  (1.0,     True,    False),
    "bulkhead": (3.0,     False,   True),
    "completo": (1.0,     True,    True),
}
config = {"protecao": "nenhuma"}

LIMITE_BULKHEAD = {"mapas": 10, "notificacao": 5}


class CircuitBreaker:
    """Estados: fechado (chama), aberto (falha rápido) e meio-aberto (deixa passar uma chamada de teste)."""

    def __init__(self, nome, janela=10, minimo_chamadas=5, taxa_falha=0.5, espera_aberto=8.0):
        self.nome = nome
        self.resultados = deque(maxlen=janela)
        self.minimo_chamadas = minimo_chamadas
        self.taxa_falha = taxa_falha
        self.espera_aberto = espera_aberto
        self.estado = "fechado"
        self.aberto_em = 0.0
        self.teste_em_andamento = False
        self.lock = threading.Lock()

    def permitir(self) -> bool:
        with self.lock:
            if self.estado == "aberto":
                if time.time() - self.aberto_em < self.espera_aberto:
                    return False
                self.estado, self.teste_em_andamento = "meio-aberto", False
            if self.estado == "meio-aberto":
                if self.teste_em_andamento:
                    return False
                self.teste_em_andamento = True
            return True

    def registrar(self, sucesso: bool):
        with self.lock:
            if self.estado == "meio-aberto":
                self.teste_em_andamento = False
                if sucesso:
                    self.estado = "fechado"
                    self.resultados.clear()
                else:
                    self.estado, self.aberto_em = "aberto", time.time()
                return
            self.resultados.append(sucesso)
            falhas = sum(1 for r in self.resultados if not r)
            if len(self.resultados) >= self.minimo_chamadas and falhas / len(self.resultados) >= self.taxa_falha:
                self.estado, self.aberto_em = "aberto", time.time()

    def resetar(self):
        with self.lock:
            self.resultados.clear()
            self.estado, self.teste_em_andamento = "fechado", False


breakers = {"mapas": CircuitBreaker("mapas"), "notificacao": CircuitBreaker("notificacao")}
bulkheads = {nome: threading.BoundedSemaphore(n) for nome, n in LIMITE_BULKHEAD.items()}
em_uso = {nome: 0 for nome in LIMITE_BULKHEAD}
contadores = {k: 0 for k in ("mapas_ok", "mapas_fallback", "mapas_circuito_aberto", "mapas_erro",
                              "notif_ok", "notif_adiada", "notif_circuito_aberto", "notif_erro")}
trava = threading.Lock()


def contar(chave):
    with trava:
        contadores[chave] += 1


@asynccontextmanager
async def ciclo_de_vida(_app):
    # A capacidade do serviço: quantas requisições ele processa ao mesmo tempo.
    anyio.to_thread.current_default_thread_limiter().total_tokens = THREADS
    yield


app = FastAPI(title="Cotação LunaLog", lifespan=ciclo_de_vida)


def chamar(dependencia: str, metodo: str, url: str, params=None):
    """Chama uma dependência aplicando a proteção ativa. Levanta em caso de falha."""
    timeout, usa_breaker, usa_bulkhead = PROTECOES[config["protecao"]]
    breaker = breakers[dependencia]

    if usa_breaker and not breaker.permitir():
        raise CircuitoAberto(dependencia)

    if usa_bulkhead and not bulkheads[dependencia].acquire(blocking=False):
        raise BulkheadCheio(dependencia)
    try:
        with trava:
            em_uso[dependencia] += 1
        try:
            r = httpx.request(metodo, url, params=params, timeout=timeout)
            r.raise_for_status()
            if usa_breaker:
                breaker.registrar(True)
            return r.json()
        except Exception:
            if usa_breaker:
                breaker.registrar(False)
            raise
        finally:
            with trava:
                em_uso[dependencia] -= 1
    finally:
        if usa_bulkhead:
            bulkheads[dependencia].release()


class CircuitoAberto(Exception):
    pass


class BulkheadCheio(Exception):
    pass


@app.get("/cotacao/{entrega_id}")
def cotacao(entrega_id: str, response: Response):
    """Calcula o frete. A rota vem da API de mapas; sem ela, usa uma estimativa (fallback)."""
    try:
        rota = chamar("mapas", "GET", f"{URL_MAPAS}/rota", {"origem": "SP", "destino": entrega_id})
        contar("mapas_ok")
        origem, km = "mapas", rota["distancia_km"]
    except CircuitoAberto:
        contar("mapas_circuito_aberto")
        origem, km = "fallback (circuito aberto)", 40.0
    except BulkheadCheio:
        contar("mapas_fallback")
        origem, km = "fallback (bulkhead cheio)", 40.0
    except Exception:
        contar("mapas_erro")
        if config["protecao"] == "nenhuma":
            raise HTTPException(504, "mapas indisponivel")
        origem, km = "fallback (erro)", 40.0
    response.headers["X-Origem"] = origem
    return {"entrega": entrega_id, "distancia_km": km, "frete": round(8 + km * 0.9, 2), "origem_distancia": origem}


@app.post("/entregas/{entrega_id}/notificar", status_code=200)
def notificar(entrega_id: str, response: Response):
    """Avisa o cliente. É secundário: se não der agora, a notificação pode ser adiada."""
    try:
        chamar("notificacao", "POST", f"{URL_NOTIFICACAO}/enviar")
        contar("notif_ok")
        return {"entrega": entrega_id, "notificacao": "enviada"}
    except (CircuitoAberto, BulkheadCheio) as e:
        contar("notif_circuito_aberto" if isinstance(e, CircuitoAberto) else "notif_adiada")
        response.status_code = 202
        return {"entrega": entrega_id, "notificacao": "adiada"}
    except Exception:
        contar("notif_erro")
        if config["protecao"] == "nenhuma":
            raise HTTPException(504, "notificacao indisponivel")
        response.status_code = 202
        return {"entrega": entrega_id, "notificacao": "adiada"}


@app.get("/tracking/{entrega_id}")
def tracking(entrega_id: str):
    """Não depende de ninguém. Serve para ver o dano colateral de uma dependência lenta."""
    return {"entrega": entrega_id, "status": "em_rota"}


@app.post("/config")
async def configurar(protecao: str):
    if protecao not in PROTECOES:
        raise HTTPException(400, f"protecao invalida; use uma de {list(PROTECOES)}")
    config["protecao"] = protecao
    for b in breakers.values():
        b.resetar()
    with trava:
        for k in contadores:
            contadores[k] = 0
    return {"protecao": protecao}


# async de propósito: o painel precisa responder mesmo com o pool de threads esgotado
@app.get("/estado")
async def estado():
    timeout, usa_breaker, usa_bulkhead = PROTECOES[config["protecao"]]
    with trava:
        return {
            "protecao": config["protecao"],
            "timeout_s": timeout,
            "circuit_breaker": {n: b.estado for n, b in breakers.items()} if usa_breaker else "desligado",
            "bulkhead": LIMITE_BULKHEAD if usa_bulkhead else "desligado",
            "chamadas_em_andamento": dict(em_uso),
            "contadores": dict(contadores),
        }
