"""O serviço NOVO sem Anti-corruption Layer: o modelo do legado contamina o design (lab 8C).

Repare nos sinais de contaminação, todos marcados com [C]:
  - os nomes da API são os do legado (COD_ENT, ST, DT_PREV, VLR, TRANSP)
  - as regras de negócio dependem de códigos numéricos e de formatos de texto do legado
  - o serviço novo "sabe" que a data vem em dd/mm/aaaa e que o valor tem vírgula
Uma mudança de formato no legado quebra o serviço novo.
"""
import os
from datetime import date, datetime

import httpx
from fastapi import FastAPI, HTTPException

LEGADO = os.environ.get("LEGADO_URL", "http://legado:8000")
app = FastAPI(title="LunaLog novo (sem ACL)")
http = httpx.Client(timeout=5)


@app.get("/entregas/{entrega_id}")
def obter(entrega_id: str):
    r = http.get(f"{LEGADO}/entregas/{entrega_id}")
    if r.status_code == 404:
        raise HTTPException(404, "nao encontrada")
    d = r.json()

    # [C] regra de negócio escrita nos termos do legado: ST == 2 significa "em rota"
    previsao = datetime.strptime(d["DT_PREV"], "%d/%m/%Y").date()          # [C] assume dd/mm/aaaa
    atrasada = int(d["ST"]) == 2 and previsao < date(2026, 11, 2)         # [C] assume status numérico (e a data "de hoje" fixa do lab)
    valor = float(d["VLR"].replace(".", "").replace(",", "."))             # [C] assume vírgula decimal e ponto de milhar

    return {"COD_ENT": d["COD_ENT"], "ST": d["ST"], "DT_PREV": d["DT_PREV"],      # [C] a API nova devolve o modelo do legado
            "VLR": d["VLR"], "TRANSP": d["TRANSP"], "atrasada": atrasada, "valor_reais": valor}
