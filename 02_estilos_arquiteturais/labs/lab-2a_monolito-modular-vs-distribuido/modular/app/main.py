"""Monólito modular: uma aplicação, três módulos com fronteiras, uma transação."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.compartilhado.db import COL_STATUS, transacao
from app.entregas import api as entregas
from app.notificacao import api as notificacao

app = FastAPI(title="LunaLog: monolito modular")


class NovaEntrega(BaseModel):
    codigo: str
    destino: str


@app.post("/entregas", status_code=201)
def criar(e: NovaEntrega):
    try:
        with transacao() as conn:
            return entregas.registrar_entrega(conn, e.codigo, e.destino)
    except RuntimeError as erro:
        raise HTTPException(500, str(erro))


@app.get("/estado")
def estado():
    with transacao() as conn:
        def n(tabela: str) -> int:
            return conn.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]

        orfas = conn.execute(
            "SELECT count(*) FROM entregas e WHERE NOT EXISTS (SELECT 1 FROM notificacoes n WHERE n.entrega_id = e.id)"
        ).fetchone()[0]
        return {"entregas": n("entregas"), "rotas": n("rotas"), "notificacoes": n("notificacoes"),
                "entregas_sem_notificacao": orfas, "coluna_status": COL_STATUS}


@app.post("/admin/falha/notificacao")
def falha(ligada: bool):
    notificacao.definir_falha(ligada)
    return {"notificacao_com_falha": ligada}


@app.post("/admin/limpar")
def limpar():
    with transacao() as conn:
        conn.execute("TRUNCATE entregas, rotas, notificacoes RESTART IDENTITY")
    return {"ok": True}
