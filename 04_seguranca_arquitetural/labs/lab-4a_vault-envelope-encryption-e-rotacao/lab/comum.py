"""Funções compartilhadas pelos scripts do lab: acesso ao Vault, ao banco e envelope encryption."""
import base64
import os

import httpx
import psycopg
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VAULT = os.environ.get("VAULT_ADDR", "http://localhost:8200")
ROOT_TOKEN = os.environ.get("ROOT_TOKEN", "root-lab")      # token raiz do lab (administração)
APP_TOKEN = os.environ.get("APP_TOKEN", "app-lab-token")   # token da aplicação (política mínima)
DB_ADMIN_URL = os.environ.get("DATABASE_ADMIN_URL", "postgresql://admin:admin-lab@localhost:5432/loja")


class ErroDoVault(Exception):
    def __init__(self, status: int, mensagens: list[str]):
        limpas = [" ".join(m.split()) for m in mensagens]
        super().__init__(f"http {status}: {'; '.join(limpas)}")
        self.status = status


def vault(metodo: str, caminho: str, token: str, corpo: dict | None = None) -> dict:
    r = httpx.request(metodo, f"{VAULT}/v1/{caminho}", headers={"X-Vault-Token": token}, json=corpo, timeout=30)
    if r.status_code >= 400:
        raise ErroDoVault(r.status_code, r.json().get("errors", [r.text]))
    return r.json() if r.content else {}


def b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode()


def desb64(texto: str) -> bytes:
    return base64.b64decode(texto)


def banco():
    return psycopg.connect(DB_ADMIN_URL, autocommit=True)


# ---- envelope encryption --------------------------------------------------------------------

def cifrar_com_envelope(dado: bytes, associado: bytes, token: str = APP_TOKEN):
    """1. gera uma DEK nova; 2. cifra o dado com ela; 3. pede ao Vault que cifre a DEK com a KEK."""
    dek = os.urandom(32)
    nonce = os.urandom(12)
    cifrado = AESGCM(dek).encrypt(nonce, dado, associado)
    dek_cifrada = vault("POST", "transit/encrypt/kek", token, {"plaintext": b64(dek)})["data"]["ciphertext"]
    return cifrado, nonce, dek_cifrada


def decifrar_com_envelope(cifrado: bytes, nonce: bytes, dek_cifrada: str, associado: bytes, token: str = APP_TOKEN) -> bytes:
    """1. pede ao Vault que decifre a DEK; 2. decifra o dado com ela."""
    dek = desb64(vault("POST", "transit/decrypt/kek", token, {"ciphertext": dek_cifrada})["data"]["plaintext"])
    return AESGCM(dek).decrypt(nonce, cifrado, associado)


def versao_da_dek(dek_cifrada: str) -> str:
    return dek_cifrada.split(":")[1]     # "vault:v2:..." -> "v2"
