"""O serviço NOVO com ACL e Branch by Abstraction (lab 8C).

A API devolve o modelo LIMPO do domínio. De onde vêm os dados é decidido por uma flag em tempo de
execução (POST /admin/fonte), sem novo deploy e com rollback imediato.
"""
import os
from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import acl
from dominio import Entrega, StatusEntrega
from fonte import FonteLegado, FontePropria

app = FastAPI(title="LunaLog novo (com ACL e Branch by Abstraction)")

FONTES = {"legado": FonteLegado(os.environ.get("LEGADO_URL", "http://legado:8000")), "proprio": FontePropria()}
flag = {"fonte": os.environ.get("FONTE_INICIAL", "legado")}


def fonte():
    return FONTES[flag["fonte"]]


def apresentar(e: Entrega) -> dict:
    return {"id": e.id, "status": e.status.value, "previsao": e.previsao.isoformat(),
            "valor": {"centavos": e.valor_centavos, "moeda": "BRL"},
            "transportadora": {"id": e.transportadora.id, "nome": e.transportadora.nome},
            "atrasada": e.atrasada(), "fonte": flag["fonte"]}


@app.get("/entregas/{entrega_id}")
def obter(entrega_id: str):
    try:
        entrega = fonte().obter(entrega_id)
    except acl.ErroDeTraducao as erro:
        # a ACL falha de forma clara: o dado estranho NÃO entra no domínio
        raise HTTPException(502, f"o legado devolveu algo que a ACL nao sabe traduzir: {erro}")
    if entrega is None:
        raise HTTPException(404, "nao encontrada")
    return apresentar(entrega)


class NovaEntrega(BaseModel):
    id: str
    status: StatusEntrega
    previsao: date
    valor_centavos: int
    transportadora_id: str


@app.post("/entregas", status_code=201)
def criar(n: NovaEntrega):
    transportadoras = {t.id: t for t in acl.TRANSPORTADORAS.values()}
    if n.transportadora_id not in transportadoras:
        raise HTTPException(422, "transportadora desconhecida")
    entrega = Entrega(n.id, n.status, n.previsao, n.valor_centavos, transportadoras[n.transportadora_id])
    fonte().salvar(entrega)
    return apresentar(entrega)


class MudancaDeFonte(BaseModel):
    fonte: str


@app.get("/admin/fonte")
def ver_fonte():
    return {"fonte": flag["fonte"], "opcoes": list(FONTES)}


@app.post("/admin/fonte")
def trocar_fonte(m: MudancaDeFonte):
    if m.fonte not in FONTES:
        raise HTTPException(422, f"fonte invalida; opcoes: {list(FONTES)}")
    flag["fonte"] = m.fonte
    return {"fonte": flag["fonte"]}
