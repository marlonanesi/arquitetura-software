"""A API, com os lados de COMANDO e de CONSULTA separados (CQRS).

  /comandos/...   validam as regras sobre o agregado (reconstruído dos eventos) e acrescentam eventos
  /consultas/...  leem os modelos de leitura (projeções): rápidas, sem regras, eventualmente consistentes
  /consultas/entregas/{id}/historico e .../em  leem o próprio event store (a fonte da verdade)
"""
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import store
from dominio import Entrega, ErroDeDominio, atualizar_esquema

app = FastAPI(title="LunaLog: CQRS e Event Sourcing")


class Comando(BaseModel):
    ator: str = "sistema"
    versao_esperada: int | None = None        # controle otimista: "só aplique se a entrega ainda estiver nesta versão"


class Registro(Comando):
    codigo: str
    transportadora: str
    previsao: str
    lat: float
    lon: float


class Confirmacao(Comando):
    lat: float
    lon: float


class Reagendamento(Comando):
    nova_previsao: str
    motivo: str = "nao_informado"


class Cancelamento(Comando):
    motivo: str


class Rota(Comando):
    motorista: str


def executar(entrega_id: str, comando: Comando, acao) -> dict:
    with store.conectar() as c:
        entrega = Entrega.reconstruir(entrega_id, store.ler_fluxo(c, entrega_id))
        if comando.versao_esperada is not None and comando.versao_esperada != entrega.versao:
            raise HTTPException(409, f"conflito: a entrega esta na versao {entrega.versao}, nao na {comando.versao_esperada}")
        try:
            eventos = acao(entrega)
        except ErroDeDominio as erro:
            raise HTTPException(422, str(erro))
        try:
            store.acrescentar(c, entrega_id, entrega.versao, eventos)
        except store.ConflitoDeVersao as erro:
            raise HTTPException(409, str(erro))
    return {"entrega": entrega_id, "eventos_gravados": [e["tipo"] for e in eventos], "versao": entrega.versao + len(eventos)}


@app.post("/comandos/entregas/{entrega_id}/registrar", status_code=201)
def registrar(entrega_id: str, r: Registro):
    return executar(entrega_id, r, lambda e: e.registrar(r.codigo, r.transportadora, r.previsao, r.lat, r.lon, r.ator))


@app.post("/comandos/entregas/{entrega_id}/iniciar-rota")
def iniciar_rota(entrega_id: str, r: Rota):
    return executar(entrega_id, r, lambda e: e.iniciar_rota(r.motorista, r.ator))


@app.post("/comandos/entregas/{entrega_id}/reagendar")
def reagendar(entrega_id: str, r: Reagendamento):
    return executar(entrega_id, r, lambda e: e.reagendar(r.nova_previsao, r.motivo, r.ator))


@app.post("/comandos/entregas/{entrega_id}/confirmar")
def confirmar(entrega_id: str, r: Confirmacao):
    return executar(entrega_id, r, lambda e: e.confirmar(r.lat, r.lon, r.ator))


@app.post("/comandos/entregas/{entrega_id}/cancelar")
def cancelar(entrega_id: str, r: Cancelamento):
    return executar(entrega_id, r, lambda e: e.cancelar(r.motivo, r.ator))


# ---------------- consultas (lado de leitura) ----------------

@app.get("/consultas/entregas/{entrega_id}")
def estado_atual(entrega_id: str):
    with store.conectar() as c:
        linha = c.execute("SELECT id, codigo, status, previsao, transportadora, reagendamentos, versao FROM proj_entregas WHERE id = %s", (entrega_id,)).fetchone()
        versao_real = c.execute("SELECT coalesce(max(versao), 0) FROM eventos WHERE agregado_id = %s", (entrega_id,)).fetchone()[0]
    if linha is None:
        raise HTTPException(404, "ainda nao esta no modelo de leitura (ou nao existe)")
    campos = ["id", "codigo", "status", "previsao", "transportadora", "reagendamentos", "versao"]
    return {**dict(zip(campos, linha)), "versao_no_event_store": versao_real, "defasagem": versao_real - linha[6]}


@app.get("/consultas/painel")
def painel():
    with store.conectar() as c:
        linhas = c.execute("SELECT transportadora, registradas, em_rota, entregues, canceladas, reagendamentos FROM proj_painel ORDER BY transportadora").fetchall()
    campos = ["transportadora", "registradas", "em_rota", "entregues", "canceladas", "reagendamentos"]
    return [dict(zip(campos, l)) for l in linhas]


@app.get("/consultas/entregas/{entrega_id}/historico")
def historico(entrega_id: str):
    with store.conectar() as c:
        eventos = store.ler_fluxo(c, entrega_id)
    if not eventos:
        raise HTTPException(404, "sem eventos")
    return [{"versao": i, "tipo": e["tipo"], "esquema": e["esquema"], "dados": e["dados"], "ator": e["ator"], "em": e["ocorrido_em"].isoformat()}
            for i, e in enumerate(eventos, 1)]


@app.get("/consultas/entregas/{entrega_id}/em")
def estado_em(entrega_id: str, instante: str):
    """Viagem no tempo: o estado da entrega em um instante do passado, reconstruído dos eventos."""
    with store.conectar() as c:
        eventos = store.ler_fluxo(c, entrega_id, ate=instante)
    if not eventos:
        raise HTTPException(404, "a entrega ainda nao existia neste instante")
    e = Entrega.reconstruir(entrega_id, eventos)
    return {"instante": instante, "status": e.status, "previsao": e.previsao, "reagendamentos": e.reagendamentos, "versao": e.versao}


@app.post("/admin/atraso")
def atraso_do_projetor(ms: int):
    with store.conectar() as c:
        c.execute("UPDATE projetor_controle SET valor = %s WHERE nome = 'atraso_ms'", (ms,))
    return {"atraso_ms": ms}


@app.post("/admin/evento-antigo")
def evento_antigo(entrega_id: str):
    """Só para o lab: grava um EntregaReagendada no formato ANTIGO (v1, sem o motivo), como se fosse de antes da mudança."""
    with store.conectar() as c:
        entrega = Entrega.reconstruir(entrega_id, store.ler_fluxo(c, entrega_id))
        store.acrescentar(c, entrega_id, entrega.versao, [{"tipo": "EntregaReagendada", "esquema": 1, "dados": {"nova_previsao": "2026-12-20"}, "ator": "legado"}])
    return {"ok": True}
