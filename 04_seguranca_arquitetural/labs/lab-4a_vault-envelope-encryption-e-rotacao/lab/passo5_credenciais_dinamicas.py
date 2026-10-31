"""Passo 5: credenciais de banco dinâmicas. Um usuário novo a cada pedido, com prazo, revogável na hora."""
import time
from urllib.parse import quote

import psycopg

from comum import APP_TOKEN, ROOT_TOKEN, banco, vault
import os

HOST = os.environ.get("DATABASE_HOST", "localhost")


def conectar(usuario: str, senha: str):
    return psycopg.connect(f"postgresql://{quote(usuario)}:{quote(senha)}@{HOST}:5432/loja", connect_timeout=5)


def pedir_credencial():
    r = vault("GET", "database/creds/app", APP_TOKEN)
    return r["data"]["username"], r["data"]["password"], r["lease_id"], r["lease_duration"]


print("A senha ESTATICA tem um problema: vive em arquivos e variaveis, e quase nunca e trocada.")
print("Aqui, a aplicacao pede uma credencial ao Vault toda vez que precisa:\n")

u1, s1, lease1, ttl = pedir_credencial()
u2, s2, lease2, _ = pedir_credencial()
print(f"1. dois pedidos, dois usuarios diferentes (prazo de {ttl} s):")
print(f"   {u1}\n   {u2}\n")

with conectar(u1, s1) as conn:
    eu = conn.execute("SELECT current_user").fetchone()[0]
    n = conn.execute("SELECT count(*) FROM registros").fetchone()[0]
    print(f"2. a aplicacao conecta como {eu} e le {n} registros")
    try:
        conn.execute("DELETE FROM registros")
    except psycopg.errors.InsufficientPrivilege as erro:
        print(f"   e o privilegio minimo vale: DELETE negado ({str(erro).splitlines()[0]})")
    conn.rollback()

with banco() as admin:
    ativos = [r[0] for r in admin.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'v-%' ORDER BY rolname")]
    print(f"\n3. usuarios temporarios existentes no PostgreSQL agora: {len(ativos)}")

vault("PUT", "sys/leases/revoke", ROOT_TOKEN, {"lease_id": lease1})
print("\n4. o administrador revoga o lease do primeiro usuario:")
try:
    conectar(u1, s1)
    print("   ERRO: ainda conectou")
except psycopg.OperationalError as erro:
    print(f"   login falha na hora: {str(erro).splitlines()[0]}")

with banco() as admin:
    ativos = [r[0] for r in admin.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'v-%' ORDER BY rolname")]
    print(f"   usuarios temporarios restantes: {len(ativos)} (o revogado foi apagado do banco)")

print(f"\n5. e o segundo usuario? Sem revogacao, expira sozinho em {ttl} s. Esperando...")
time.sleep(ttl + 3)
try:
    conectar(u2, s2)
    print("   ainda conecta (o Vault remove o usuario ao expirar o lease; confira em alguns segundos)")
except psycopg.OperationalError as erro:
    print(f"   expirou: {str(erro).splitlines()[0]}")
