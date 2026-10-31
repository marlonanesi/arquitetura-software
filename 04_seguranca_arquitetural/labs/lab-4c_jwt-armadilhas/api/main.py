"""API de tracking da LunaLog com dois validadores de JWT lado a lado.

  /vulneravel/entregas/{id}  : validador ingênuo, com falhas clássicas (apenas para estudo)
  /correto/entregas/{id}     : validador correto

ATENÇÃO: o validador ingênuo é DE PROPÓSITO inseguro. Nunca copie esse código para um sistema real.
"""
import base64
import hashlib
import hmac
import json
import os
import urllib.request

import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse

ISSUER = os.environ["ISSUER"]
JWKS_URL = os.environ["JWKS_URL"]
AUDIENCE = os.environ["AUDIENCE"]

app = FastAPI(title="Tracking API (lab 4C)")

_chaves: dict[str, rsa.RSAPublicKey] = {}
_pem_publica: dict[str, str] = {}


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def carregar_chaves():
    """Busca as chaves públicas no endpoint JWKS do provedor de identidade."""
    if _chaves:
        return
    try:
        with urllib.request.urlopen(JWKS_URL, timeout=5) as r:
            jwks = json.load(r)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"provedor de identidade indisponivel: {e}")
    for k in jwks["keys"]:
        if k.get("use") == "sig" and k.get("kty") == "RSA":
            n = int.from_bytes(b64url_decode(k["n"]), "big")
            e = int.from_bytes(b64url_decode(k["e"]), "big")
            chave = rsa.RSAPublicNumbers(e, n).public_key()
            _chaves[k["kid"]] = chave
            _pem_publica[k["kid"]] = chave.public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()


@app.get("/chave-publica.pem", response_class=PlainTextResponse)
def chave_publica():
    """A chave pública é pública por definição: qualquer cliente pode (e deve) poder baixá-la."""
    carregar_chaves()
    return next(iter(_pem_publica.values()))


# ---------------------------------------------------------------------------------------------
# VALIDADOR INGÊNUO (de propósito): reúne as falhas mais comuns em implementações reais
# ---------------------------------------------------------------------------------------------
def validar_ingenuo(token: str) -> dict:
    carregar_chaves()
    try:
        h_b64, p_b64, s_b64 = token.split(".")
        cabecalho = json.loads(b64url_decode(h_b64))
        payload = json.loads(b64url_decode(p_b64))
    except Exception:
        raise HTTPException(401, "token malformado")

    entrada = f"{h_b64}.{p_b64}".encode()
    alg = cabecalho.get("alg")  # FALHA 1: confia no algoritmo que o PRÓPRIO TOKEN diz que usa

    if alg == "none":
        return payload  # FALHA 2: aceita token sem assinatura

    assinatura = b64url_decode(s_b64)
    if alg == "HS256":
        # FALHA 3: confusão de algoritmo. Usa a chave pública (que todo mundo conhece) como segredo HMAC.
        segredo = next(iter(_pem_publica.values())).encode()
        esperado = hmac.new(segredo, entrada, hashlib.sha256).digest()
        if not hmac.compare_digest(esperado, assinatura):
            raise HTTPException(401, "assinatura invalida")
    elif alg == "RS256":
        chave = _chaves.get(cabecalho.get("kid"))
        if chave is None:
            raise HTTPException(401, "kid desconhecido")
        try:
            chave.verify(assinatura, entrada, padding.PKCS1v15(), hashes.SHA256())
        except Exception:
            raise HTTPException(401, "assinatura invalida")
    else:
        raise HTTPException(401, "algoritmo nao suportado")

    # FALHA 4: nunca confere a expiração (exp)
    # FALHA 5: nunca confere para quem o token foi emitido (aud) nem quem o emitiu (iss)
    return payload


# ---------------------------------------------------------------------------------------------
# VALIDADOR CORRETO
# ---------------------------------------------------------------------------------------------
_jwk_client = jwt.PyJWKClient(JWKS_URL, cache_keys=True)


def validar_correto(token: str) -> dict:
    try:
        chave = _jwk_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            chave.key,
            algorithms=["RS256"],               # lista fixa no servidor, nunca o que o token diz
            audience=AUDIENCE,                  # o token tem que ser PARA esta API
            issuer=ISSUER,                      # e emitido pelo provedor que esperamos
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},  # e expira
            leeway=0,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expirado")
    except jwt.InvalidAudienceError:
        raise HTTPException(401, "audience invalida: o token nao e para esta API")
    except jwt.InvalidIssuerError:
        raise HTTPException(401, "issuer invalido")
    except (jwt.PyJWTError, jwt.PyJWKClientError) as e:
        raise HTTPException(401, f"token invalido: {type(e).__name__}")


def extrair(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "faltou o header Authorization: Bearer <token>")
    return authorization.split(" ", 1)[1].strip()


def resposta(entrega_id: str, payload: dict, validador: str) -> dict:
    return {
        "validador": validador,
        "entrega": entrega_id,
        "status": "em_rota",
        "autenticado_como": payload.get("preferred_username") or payload.get("azp") or payload.get("sub"),
        "papeis": payload.get("realm_access", {}).get("roles", payload.get("roles", [])),
    }


@app.get("/vulneravel/entregas/{entrega_id}")
def entrega_vulneravel(entrega_id: str, authorization: str | None = Header(default=None)):
    return resposta(entrega_id, validar_ingenuo(extrair(authorization)), "ingenuo")


@app.get("/correto/entregas/{entrega_id}")
def entrega_correta(entrega_id: str, authorization: str | None = Header(default=None)):
    return resposta(entrega_id, validar_correto(extrair(authorization)), "correto")
