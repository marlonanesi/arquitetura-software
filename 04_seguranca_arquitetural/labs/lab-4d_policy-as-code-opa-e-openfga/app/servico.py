"""Um microsserviço que NÃO decide autorização: ele pergunta a um ponto de decisão (PDP) externo.

O mesmo código roda os dois serviços do lab, escolhidos por SERVICO:
  SERVICO=rotas     GET /rotas/{id}
  SERVICO=entregas  GET /entregas/{id}

O PDP é escolhido por PDP (rbac, abac ou rebac) e pode ser trocado por requisição com ?pdp=...
(só para o laboratório comparar os três modelos; em um sistema real haveria um só).

  rbac, abac -> OPA (Rego)         POST /v1/data/lunalog/<modelo>/allow
  rebac      -> OpenFGA            POST /stores/{id}/check
Se o PDP não responder, o serviço NEGA (fail closed).
"""
import json
import os

import httpx
from fastapi import FastAPI, Header, HTTPException

SERVICO = os.environ["SERVICO"]
PDP_PADRAO = os.environ.get("PDP", "abac")
OPA_URL = os.environ.get("OPA_URL", "http://opa:8181")
FGA_URL = os.environ.get("FGA_URL", "http://openfga:8080")

CATALOGO = json.load(open(f"/app/catalogos/{SERVICO}.json", encoding="utf-8"))
TIPO_FGA = "rota" if SERVICO == "rotas" else "entrega"
app = FastAPI(title=f"LunaLog: servico de {SERVICO}")
cliente = httpx.AsyncClient(timeout=3.0)
_store_id: dict[str, str] = {}


async def store_id() -> str:
    if "id" not in _store_id:
        lojas = (await cliente.get(f"{FGA_URL}/stores")).json()["stores"]
        mais_recente = max((l for l in lojas if l["name"] == "lunalog"), key=lambda l: l["created_at"])
        _store_id["id"] = mais_recente["id"]
    return _store_id["id"]


async def decidir(pdp: str, usuario: str, rid: str, recurso: dict, hora: int) -> bool:
    if pdp in ("rbac", "abac"):
        entrada = {"input": {
            "usuario": usuario, "acao": "ver", "hora": hora,
            "recurso": {"tipo": SERVICO, "id": rid, "transportadora": recurso["transportadora"],
                        "filial": recurso["filial"], "motorista": recurso["motorista"]},
        }}
        r = await cliente.post(f"{OPA_URL}/v1/data/lunalog/{pdp}/allow", json=entrada)
        r.raise_for_status()
        return r.json().get("result", False) is True
    if pdp == "rebac":
        corpo = {"tuple_key": {"user": f"usuario:{usuario}", "relation": "viewer", "object": f"{TIPO_FGA}:{rid}"}}
        r = await cliente.post(f"{FGA_URL}/stores/{await store_id()}/check", json=corpo)
        r.raise_for_status()
        return r.json().get("allowed", False) is True
    raise HTTPException(400, f"pdp desconhecido: {pdp}")


@app.get(f"/{SERVICO}/{{rid}}")
async def obter(rid: str, pdp: str = "", x_usuario: str = Header(default=""), x_hora: int = Header(default=10)):
    recurso = CATALOGO.get(rid)
    if recurso is None:
        raise HTTPException(404, "nao encontrado")
    try:
        permitido = await decidir(pdp or PDP_PADRAO, x_usuario, rid, recurso, x_hora)
    except (httpx.HTTPError, KeyError, ValueError) as erro:
        raise HTTPException(503, f"ponto de decisao indisponivel ({erro.__class__.__name__}): acesso negado por seguranca")
    if not permitido:
        raise HTTPException(403, "acesso negado")
    return {"id": rid, **recurso}
