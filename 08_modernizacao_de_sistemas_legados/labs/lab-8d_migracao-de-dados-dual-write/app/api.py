"""O serviço de entregas durante a migração: escreve e lê conforme as FLAGS (lab 8D).

  escrita:  legado   só o banco legado (o ponto de partida)
            dupla    dual-write: legado primeiro (a verdade), depois o novo
            novo     o banco novo é a verdade; o legado ainda recebe uma cópia (para o rollback)
  leitura:  legado | novo | preguicosa (lê o novo; se não achar, busca no legado, migra e devolve)
  falha_novo: simula uma falha de escrita no banco novo (para ver a divergência e a reconciliação)
"""
import os
from datetime import date

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import traducao

URL_LEGADO = os.environ.get("URL_LEGADO", "postgresql://luna:luna@postgres:5432/legado")
URL_NOVO = os.environ.get("URL_NOVO", "postgresql://luna:luna@postgres:5432/novo")
app = FastAPI(title="LunaLog: entregas durante a migracao")
flags = {"escrita": "legado", "leitura": "legado", "falha_novo": False}

UPSERT_LEGADO = ("INSERT INTO entrega_tb (cod_ent, st, dt_prev, vlr, transp, dt_alt) VALUES (%s, %s, %s, %s, %s, now()) "
                 "ON CONFLICT (cod_ent) DO UPDATE SET st = EXCLUDED.st, dt_prev = EXCLUDED.dt_prev, vlr = EXCLUDED.vlr, "
                 "transp = EXCLUDED.transp, dt_alt = now()")
UPSERT_NOVO = ("INSERT INTO entregas (id, status, previsao, valor_centavos, transportadora_id, origem) VALUES (%s, %s, %s, %s, %s, %s) "
               "ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, previsao = EXCLUDED.previsao, "
               "valor_centavos = EXCLUDED.valor_centavos, transportadora_id = EXCLUDED.transportadora_id, "
               "origem = EXCLUDED.origem, atualizado_em = now()")


class Entrega(BaseModel):
    id: str
    status: str
    previsao: date
    valor_centavos: int
    transportadora_id: str


def gravar_legado(e: dict) -> None:
    with psycopg.connect(URL_LEGADO, autocommit=True) as c:
        c.execute(UPSERT_LEGADO, traducao.para_legado(e))


def gravar_novo(e: dict, origem: str) -> None:
    if flags["falha_novo"]:
        raise RuntimeError("falha simulada ao gravar no banco novo")
    with psycopg.connect(URL_NOVO, autocommit=True) as c:
        c.execute(UPSERT_NOVO, (e["id"], e["status"], e["previsao"], e["valor_centavos"], e["transportadora_id"], origem))


def registrar_reparo(cod_ent: str, motivo: str) -> None:
    with psycopg.connect(URL_LEGADO, autocommit=True) as c:
        c.execute("INSERT INTO fila_reparo (cod_ent, motivo) VALUES (%s, %s)", (cod_ent, motivo))


@app.post("/entregas", status_code=201)
def gravar(e: Entrega):
    d = e.model_dump()
    modo = flags["escrita"]
    aviso = None
    if modo == "legado":
        gravar_legado(d)
    elif modo == "dupla":
        gravar_legado(d)                       # o legado ainda é a verdade: se ele falhar, a requisição falha
        try:
            gravar_novo(d, "dual-write")
        except Exception as erro:              # a falha no novo NÃO derruba a requisição: vira reparo
            registrar_reparo(d["id"], str(erro))
            aviso = "gravado no legado; divergencia registrada para reparo"
    elif modo == "novo":
        gravar_novo(d, "novo-primario")        # o novo é a verdade: se ele falhar, a requisição falha
        try:
            gravar_legado(d)                   # cópia para o legado, mantém o rollback possível
        except Exception as erro:
            aviso = f"gravado no novo; copia para o legado falhou: {erro}"
    return {"id": d["id"], "escrita": modo, "aviso": aviso}


def ler_legado(entrega_id: str):
    with psycopg.connect(URL_LEGADO) as c:
        linha = c.execute("SELECT cod_ent, st, dt_prev, vlr, transp FROM entrega_tb WHERE cod_ent = %s", (entrega_id,)).fetchone()
    return None if linha is None else traducao.do_legado(*linha)


def ler_novo(entrega_id: str):
    with psycopg.connect(URL_NOVO) as c:
        l = c.execute("SELECT id, status, previsao, valor_centavos, transportadora_id FROM entregas WHERE id = %s", (entrega_id,)).fetchone()
    return None if l is None else {"id": l[0], "status": l[1], "previsao": l[2], "valor_centavos": l[3], "transportadora_id": l[4]}


@app.get("/entregas/{entrega_id}")
def obter(entrega_id: str):
    modo = flags["leitura"]
    fonte = modo
    try:
        if modo == "legado":
            e = ler_legado(entrega_id)
        elif modo == "novo":
            e = ler_novo(entrega_id)
        else:                                                  # preguiçosa: migra na leitura
            e = ler_novo(entrega_id)
            fonte = "novo"
            if e is None:
                e = ler_legado(entrega_id)
                fonte = "legado (migrada agora)"
                if e is not None:
                    gravar_novo(e, "leitura")
    except traducao.ErroDeTraducao as erro:
        raise HTTPException(422, f"registro no legado nao pode ser migrado: {erro}")
    if e is None:
        raise HTTPException(404, "nao encontrada")
    return {**e, "previsao": e["previsao"].isoformat(), "fonte": fonte}


class Flags(BaseModel):
    escrita: str | None = None
    leitura: str | None = None
    falha_novo: bool | None = None


@app.get("/admin/flags")
def ver_flags():
    return flags


@app.post("/admin/flags")
def mudar_flags(f: Flags):
    if f.escrita is not None:
        if f.escrita not in ("legado", "dupla", "novo"):
            raise HTTPException(422, "escrita: legado, dupla ou novo")
        flags["escrita"] = f.escrita
    if f.leitura is not None:
        if f.leitura not in ("legado", "novo", "preguicosa"):
            raise HTTPException(422, "leitura: legado, novo ou preguicosa")
        flags["leitura"] = f.leitura
    if f.falha_novo is not None:
        flags["falha_novo"] = f.falha_novo
    return flags
