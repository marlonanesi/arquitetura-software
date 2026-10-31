"""Instância de aplicação para os experimentos de balanceamento (lab 3B).

Cada instância tem um NOME e um ATRASO_MS (capacidade diferente). O serviço de autenticação do lab
guarda a sessão NA MEMÓRIA da instância (o design stateful da aula 3.3) e também sabe emitir um token
assinado, que qualquer instância valida (o design stateless).
"""
import asyncio
import base64
import hashlib
import hmac
import os
import secrets

from fastapi import FastAPI, Header, HTTPException, Request, Response

NOME = os.environ.get("NOME", "app")
ATRASO_MS = int(os.environ.get("ATRASO_MS", "10"))
SEGREDO = os.environ.get("SEGREDO", "segredo-de-laboratorio").encode()   # fictício; igual em todas as instâncias

app = FastAPI(title=f"Instancia {NOME}")
sessoes: dict[str, str] = {}      # sessão local: existe só nesta instância
falha = {"ligada": False}


def assinar(usuario: str) -> str:
    corpo = base64.urlsafe_b64encode(usuario.encode()).decode().rstrip("=")
    assinatura = hmac.new(SEGREDO, corpo.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{corpo}.{assinatura}"


def validar_assinado(token: str) -> str | None:
    corpo, _, assinatura = token.partition(".")
    esperado = hmac.new(SEGREDO, corpo.encode(), hashlib.sha256).hexdigest()[:24]
    if not hmac.compare_digest(assinatura, esperado):
        return None
    return base64.urlsafe_b64decode(corpo + "=" * (-len(corpo) % 4)).decode()


@app.get("/")
async def raiz(response: Response):
    await asyncio.sleep(ATRASO_MS / 1000)
    response.headers["X-Instancia"] = NOME
    return {"instancia": NOME}


@app.get("/api/{recurso}")
async def api(recurso: str, response: Response):
    await asyncio.sleep(ATRASO_MS / 1000)
    response.headers["X-Instancia"] = NOME
    return {"instancia": NOME, "recurso": recurso}


@app.post("/login")
async def login(response: Response, assinada: int = 0):
    response.headers["X-Instancia"] = NOME
    if assinada:
        return {"token": assinar("transportadora-42"), "tipo": "assinado", "instancia": NOME}
    token = secrets.token_hex(8)
    sessoes[token] = "transportadora-42"
    return {"token": token, "tipo": "sessao-local", "instancia": NOME}


@app.get("/perfil")
async def perfil(response: Response, authorization: str = Header(default="")):
    response.headers["X-Instancia"] = NOME
    token = authorization.removeprefix("Bearer ").strip()
    usuario = sessoes.get(token) or (validar_assinado(token) if "." in token else None)
    if usuario is None:
        raise HTTPException(401, f"sessao desconhecida na instancia {NOME}", headers={"X-Instancia": NOME})
    return {"usuario": usuario, "instancia": NOME}


@app.get("/saude")
async def saude():
    if falha["ligada"]:
        raise HTTPException(503, "instancia com falha")
    return {"status": "ok", "instancia": NOME}


@app.post("/admin/falha")
async def admin_falha(ligada: bool):
    falha["ligada"] = ligada
    return {"falha": ligada}
