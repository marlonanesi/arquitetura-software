"""API de entregas da LunaLog DEPOIS DO REDESIGN (lab 4E). Compare com app/inseguro/main.py.

Cada correção está marcada com [Cx] e responde a uma falha [Fx] do sistema original.
"""
import hashlib
import hmac
import math
import os
import time
from datetime import datetime, timezone

import jwt
import psycopg
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

SECRET = os.environ["JWT_SECRET"]                 # [C1] o segredo vem do ambiente, nunca do código
DATABASE_URL = os.environ["DATABASE_URL"]         # [C8] credencial própria desta API, com privilégio mínimo
EXPIRACAO_S = 15 * 60                              # [C2] token curto
RAIO_CONFIRMACAO_M = 100

app = FastAPI(title="LunaLog Entregas (redesenhado)")


def conn():
    return psycopg.connect(DATABASE_URL, autocommit=True)


class Login(BaseModel):
    nome: str
    senha: str


class Confirmacao(BaseModel):
    lat: float
    lon: float
    ts: int          # horário do aparelho (epoch, segundos), para barrar repetição de requisições antigas


def verificar_senha(senha: str, armazenada: str) -> bool:
    _, sal, esperado = armazenada.split("$")
    obtido = hashlib.scrypt(senha.encode(), salt=bytes.fromhex(sal), n=2**14, r=8, p=1, dklen=32).hex()
    return hmac.compare_digest(obtido, esperado)


def usuario_do_token(authorization: str) -> dict:
    try:
        # [C2] exp obrigatório, audiência e emissor conferidos, algoritmo fixo
        return jwt.decode(authorization.removeprefix("Bearer "), SECRET, algorithms=["HS256"],
                          audience="lunalog-api", issuer="lunalog-auth", options={"require": ["exp", "aud", "iss", "sub"]})
    except jwt.PyJWTError:
        raise HTTPException(401, "token invalido ou expirado")


def distancia_m(lat1, lon1, lat2, lon2) -> float:
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


@app.post("/login")
def login(d: Login):
    with conn() as c:
        # [C3] consulta parametrizada; a senha é comparada por hash (scrypt), nunca em texto puro
        linha = c.execute("SELECT id, nome, papel, senha_hash FROM usuarios WHERE nome = %s", (d.nome,)).fetchone()
    if linha is None or not verificar_senha(d.senha, linha[3]):
        raise HTTPException(401, "credenciais invalidas")          # mesma resposta para usuário e senha errados
    agora = int(time.time())
    return {"token": jwt.encode({"sub": linha[1], "uid": linha[0], "papel": linha[2], "iat": agora,
                                 "exp": agora + EXPIRACAO_S, "aud": "lunalog-api", "iss": "lunalog-auth"}, SECRET, algorithm="HS256")}


COLUNAS = "id, codigo, destinatario, endereco, motorista_id, status"        # [C4] o CPF nem sai do banco nesta rota
CAMPOS = ["id", "codigo", "destinatario", "endereco", "motorista_id", "status"]


@app.get("/entregas")
def listar(authorization: str = Header(default="")):
    u = usuario_do_token(authorization)
    with conn() as c:
        # [C4] a autorização é decidida NO SERVIDOR: motorista vê as suas; operador vê todas
        if u["papel"] == "operador":
            linhas = c.execute(f"SELECT {COLUNAS} FROM entregas ORDER BY id").fetchall()
        else:
            linhas = c.execute(f"SELECT {COLUNAS} FROM entregas WHERE motorista_id = %s ORDER BY id", (u["uid"],)).fetchall()
    return [dict(zip(CAMPOS, l)) for l in linhas]


@app.get("/entregas/{entrega_id}")
def obter(entrega_id: int, authorization: str = Header(default="")):
    u = usuario_do_token(authorization)
    with conn() as c:
        l = c.execute(f"SELECT {COLUNAS} FROM entregas WHERE id = %s", (entrega_id,)).fetchone()
    # [C5] entrega de outro motorista responde 404 (não revela que ela existe)
    if l is None or (u["papel"] != "operador" and l[4] != u["uid"]):
        raise HTTPException(404, "nao encontrada")
    return dict(zip(CAMPOS, l))


@app.post("/entregas/{entrega_id}/confirmar")
def confirmar(entrega_id: int, d: Confirmacao, request: Request, authorization: str = Header(default="")):
    u = usuario_do_token(authorization)
    if abs(time.time() - d.ts) > 60:
        raise HTTPException(422, "horario do aparelho fora da janela de 60 s (possivel repeticao)")        # [C6]
    with conn() as c:
        l = c.execute("SELECT motorista_id, dest_lat, dest_lon, status FROM entregas WHERE id = %s", (entrega_id,)).fetchone()
        if l is None or l[0] != u["uid"]:
            raise HTTPException(404, "nao encontrada")
        if l[3] == "entregue":
            raise HTTPException(409, "entrega ja confirmada")
        distancia = distancia_m(d.lat, d.lon, l[1], l[2])
        if distancia > RAIO_CONFIRMACAO_M:                                            # [C6] a posição é validada no servidor
            raise HTTPException(422, f"posicao a {distancia:.0f} m do destino (maximo {RAIO_CONFIRMACAO_M} m)")
        c.execute("UPDATE entregas SET status = 'entregue', conf_lat = %s, conf_lon = %s WHERE id = %s", (d.lat, d.lon, entrega_id))

        # [C7] trilha de auditoria encadeada: quem, quando, de onde; cada linha amarra a anterior por hash
        anterior = c.execute("SELECT hash FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()
        hash_anterior = anterior[0] if anterior else "0" * 64
        agora = datetime.now(timezone.utc)
        origem = request.client.host if request.client else "?"
        carga = f"{hash_anterior}|{agora.isoformat()}|{u['sub']}|confirmar|{entrega_id}|{d.lat}|{d.lon}|{origem}"
        c.execute("INSERT INTO auditoria (em, usuario, acao, entrega_id, lat, lon, origem_ip, hash_anterior, hash) "
                  "VALUES (%s, %s, 'confirmar', %s, %s, %s, %s, %s, %s)",
                  (agora, u["sub"], entrega_id, d.lat, d.lon, origem, hash_anterior, hashlib.sha256(carga.encode()).hexdigest()))
    return {"ok": True, "entrega": entrega_id, "status": "entregue"}


@app.get("/relatorio")
def relatorio(authorization: str = Header(default="")):
    u = usuario_do_token(authorization)
    if u.get("papel") != "operador":
        raise HTTPException(403, "apenas operadores")
    with conn() as c:
        n = c.execute("SELECT count(*) FROM entregas WHERE status = 'entregue'").fetchone()[0]
    return {"entregues": n}


@app.get("/auditoria/{entrega_id}")
def auditoria(entrega_id: int, authorization: str = Header(default="")):
    u = usuario_do_token(authorization)
    if u.get("papel") != "operador":
        raise HTTPException(403, "apenas operadores")
    with conn() as c:
        linhas = c.execute("SELECT em, usuario, acao, lat, lon, origem_ip, hash FROM auditoria WHERE entrega_id = %s ORDER BY id", (entrega_id,)).fetchall()
    if not linhas:
        raise HTTPException(404, "sem registros")
    return [{"em": l[0].isoformat(), "usuario": l[1], "acao": l[2], "lat": l[3], "lon": l[4], "origem": l[5], "hash": l[6][:16]} for l in linhas]
