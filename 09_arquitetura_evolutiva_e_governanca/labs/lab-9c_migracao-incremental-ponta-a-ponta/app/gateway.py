"""O GATEWAY (o estrangulador): único endereço dos clientes durante a migração.

Decide, por requisição, de onde vem a resposta, consultando FLAGS no flagd (padrão OpenFeature):

  kill-switch-novo   se ligada, TUDO volta ao legado (o botão de emergência; o guardião também a aciona)
  leitura-novo       liberação gradual por usuário (fractional): o percentual vive na flag, não no código
  sombra             o novo recebe uma cópia das leituras e o resultado é COMPARADO, sem afetar o cliente
  escrita            legado, dupla (dual-write) ou novo (o novo é a verdade; o legado recebe uma cópia)

Se uma flag não puder ser avaliada (flagd fora do ar), o gateway escolhe o caminho SEGURO: o legado.
Devolve sempre o modelo limpo; a tradução do legado fica aqui (a ACL, lab 8C).
"""
import asyncio
import os
import time

import httpx
import psycopg
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

import traducao

LEGADO = os.environ.get("LEGADO_URL", "http://legado:8000")
NOVO = os.environ.get("NOVO_URL", "http://novo:8000")
FLAGD = os.environ.get("FLAGD_URL", "http://flagd:8013")
URL_LEGADO_DB = os.environ.get("URL_LEGADO", "postgresql://luna:luna@postgres:5432/legado")

app = FastAPI(title="LunaLog gateway (estrangulador)")
http = httpx.AsyncClient(timeout=3.0)
m = {k: 0 for k in ["leituras_legado", "leituras_novo", "erros_novo", "fallbacks", "sombra_iguais", "sombra_divergentes",
                    "sombra_erros_novo", "escritas_legado", "escritas_dupla", "escritas_novo", "reparos_registrados"]}
lat = {"legado": [0.0, 0], "novo": [0.0, 0]}      # soma de milissegundos e contagem


async def flag(tipo: str, chave: str, alvo: str, padrao):
    try:
        r = await http.post(f"{FLAGD}/flagd.evaluation.v1.Service/Resolve{tipo}", json={"flagKey": chave, "context": {"targetingKey": alvo}}, timeout=0.5)
        r.raise_for_status()
        return r.json()["value"]
    except Exception:
        return padrao                                    # falha ao avaliar a flag: caminho seguro


def limpo_do_legado(cod: str, d: dict) -> dict:
    e = traducao.do_legado(d["COD_ENT"], d["ST"], d["DT_PREV"], d["VLR"], d["TRANSP"])
    return {**e, "previsao": e["previsao"].isoformat()}


async def ler_legado(cod: str) -> dict | None:
    t = time.time()
    r = await http.get(f"{LEGADO}/entregas/{cod}")
    lat["legado"][0] += (time.time() - t) * 1000
    lat["legado"][1] += 1
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return limpo_do_legado(cod, r.json())


async def ler_novo(cod: str) -> dict | None:
    t = time.time()
    r = await http.get(f"{NOVO}/entregas/{cod}")
    lat["novo"][0] += (time.time() - t) * 1000
    lat["novo"][1] += 1
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


async def comparar_em_sombra(cod: str, do_legado: dict | None) -> None:
    try:
        do_novo = await ler_novo(cod)
        m["sombra_iguais" if do_novo == do_legado else "sombra_divergentes"] += 1
    except Exception:
        m["sombra_erros_novo"] += 1


@app.get("/entregas/{cod}")
async def obter(cod: str, x_usuario: str = Header(default="anonimo")):
    kill = await flag("Boolean", "kill-switch-novo", x_usuario, True)
    usar_novo = (not kill) and await flag("Boolean", "leitura-novo", x_usuario, False)
    sombra = (not kill) and await flag("Boolean", "sombra", x_usuario, False)

    if usar_novo:
        try:
            e = await ler_novo(cod)
            m["leituras_novo"] += 1
            if e is None:
                raise HTTPException(404, "nao encontrada")
            return {**e, "fonte": "novo"}
        except HTTPException:
            raise
        except Exception:
            m["erros_novo"] += 1                           # o novo falhou: o cliente NAO percebe, o legado responde
            m["fallbacks"] += 1

    e = await ler_legado(cod)
    m["leituras_legado"] += 1
    if e is None:
        raise HTTPException(404, "nao encontrada")
    if sombra and not usar_novo:
        asyncio.create_task(comparar_em_sombra(cod, e))
    return {**e, "fonte": "legado"}


class Entrega(BaseModel):
    id: str
    status: str
    previsao: str
    valor_centavos: int
    transportadora_id: str


async def gravar_legado(e: dict) -> None:
    cod, st, dt, vlr, transp = traducao.para_legado(e)
    (await http.put(f"{LEGADO}/entregas/{cod}", json={"COD_ENT": cod, "ST": st, "DT_PREV": dt, "VLR": vlr, "TRANSP": transp})).raise_for_status()


async def gravar_novo(e: dict, origem: str) -> None:
    (await http.put(f"{NOVO}/entregas/{e['id']}", params={"origem": origem}, json=e)).raise_for_status()


@app.post("/entregas", status_code=201)
async def gravar(e: Entrega, x_usuario: str = Header(default="anonimo")):
    d = e.model_dump()
    kill = await flag("Boolean", "kill-switch-novo", x_usuario, True)
    modo = "legado" if kill else await flag("String", "escrita", x_usuario, "legado")
    if modo == "legado":
        await gravar_legado(d)
        m["escritas_legado"] += 1
    elif modo == "dupla":
        await gravar_legado(d)
        m["escritas_dupla"] += 1
        try:
            await gravar_novo(d, "dual-write")
        except Exception as erro:
            m["reparos_registrados"] += 1
            with psycopg.connect(URL_LEGADO_DB, autocommit=True) as c:
                c.execute("INSERT INTO fila_reparo (cod_ent, motivo) VALUES (%s, %s)", (d["id"], str(erro)[:200]))
    else:   # novo: é a verdade; o legado recebe uma cópia para manter o rollback possível
        await gravar_novo(d, "novo-primario")
        m["escritas_novo"] += 1
        try:
            await gravar_legado(d)
        except Exception:
            pass
    return {"id": d["id"], "escrita": modo}


@app.get("/metricas")
async def metricas():
    media = lambda k: round(lat[k][0] / lat[k][1], 1) if lat[k][1] else 0
    kill = await flag("Boolean", "kill-switch-novo", "x", True)
    sombra = await flag("Boolean", "sombra", "x", False)
    escrita = await flag("String", "escrita", "x", "legado")
    return {**m, "latencia_media_ms": {"legado": media("legado"), "novo": media("novo")},
            "flags": {"kill_switch_novo": kill, "sombra": sombra, "escrita": escrita}}


@app.post("/admin/zerar")
async def zerar():
    """Começa uma nova janela de medição (zera os contadores). Útil entre os marcos."""
    for k in m:
        m[k] = 0
    for k in lat:
        lat[k] = [0.0, 0]
    return {"ok": True}
