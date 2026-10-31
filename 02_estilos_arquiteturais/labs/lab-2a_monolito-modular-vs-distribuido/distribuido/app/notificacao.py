"""Serviço de notificação: lê a entrega (no banco compartilhado) e registra o aviso."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.db import COL_STATUS, conectar

app = FastAPI(title="LunaLog distribuido: notificacao")


class Pedido(BaseModel):
    entrega_id: int
    canal: str


@app.post("/notificacoes")
def avisar(p: Pedido):
    with conectar() as conn:
        # lê direto da tabela do serviço de entregas para montar a mensagem
        linha = conn.execute(f"SELECT {COL_STATUS} FROM entregas WHERE id = %s", (p.entrega_id,)).fetchone()
        if linha is None:
            raise HTTPException(404, "entrega nao encontrada")
        conn.execute("INSERT INTO notificacoes (entrega_id, canal) VALUES (%s, %s)", (p.entrega_id, p.canal))
    return {"enviada": True}
