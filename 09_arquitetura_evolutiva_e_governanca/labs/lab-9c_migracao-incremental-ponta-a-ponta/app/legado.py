"""O serviço LEGADO: o monólito da LunaLog, com o modelo antigo (nomes crípticos, textos em formatos mistos)."""
import os

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

URL = os.environ.get("URL_LEGADO", "postgresql://luna:luna@postgres:5432/legado")
app = FastAPI(title="LunaLog legado")


class EntregaLegada(BaseModel):
    COD_ENT: str
    ST: str
    DT_PREV: str
    VLR: str
    TRANSP: str


@app.get("/entregas/{cod}")
def obter(cod: str):
    with psycopg.connect(URL) as c:
        l = c.execute("SELECT cod_ent, st, dt_prev, vlr, transp FROM entrega_tb WHERE cod_ent = %s", (cod,)).fetchone()
    if l is None:
        raise HTTPException(404, "nao encontrada")
    return dict(zip(["COD_ENT", "ST", "DT_PREV", "VLR", "TRANSP"], l))


@app.put("/entregas/{cod}")
def gravar(cod: str, e: EntregaLegada):
    with psycopg.connect(URL, autocommit=True) as c:
        c.execute("INSERT INTO entrega_tb (cod_ent, st, dt_prev, vlr, transp, dt_alt) VALUES (%s, %s, %s, %s, %s, now()) "
                  "ON CONFLICT (cod_ent) DO UPDATE SET st = EXCLUDED.st, dt_prev = EXCLUDED.dt_prev, vlr = EXCLUDED.vlr, transp = EXCLUDED.transp, dt_alt = now()",
                  (cod, e.ST, e.DT_PREV, e.VLR, e.TRANSP))
    return {"ok": True}
