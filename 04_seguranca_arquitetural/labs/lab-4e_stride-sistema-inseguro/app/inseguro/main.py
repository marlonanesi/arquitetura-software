"""API de entregas da LunaLog COMO ELA NASCEU. Insegura DE PROPÓSITO, para o diagnóstico (lab 4E).

Não use nada disto em produção. Cada falha abaixo está marcada com [Fx] e é explorada em scripts/ataques.py.
"""
import os

import jwt
import psycopg
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

SECRET = "luna-secret-123"      # [F1] segredo no código (e no repositório)
DATABASE_URL = os.environ["DATABASE_URL"]   # [F8] o mesmo usuário administrador de banco em todos os serviços

app = FastAPI(title="LunaLog Entregas (inseguro)")


def conn():
    return psycopg.connect(DATABASE_URL, autocommit=True)


class Login(BaseModel):
    nome: str
    senha: str


class Confirmacao(BaseModel):
    lat: float
    lon: float


def usuario_do_token(authorization: str) -> dict:
    try:
        # [F2] o token não tem expiração, e a assinatura usa o segredo fixo do código
        return jwt.decode(authorization.removeprefix("Bearer "), SECRET, algorithms=["HS256"], options={"verify_exp": False})
    except jwt.PyJWTError:
        raise HTTPException(401, "token invalido")


@app.post("/login")
def login(d: Login):
    # [F3] SQL montado por concatenação de texto: injeção de SQL
    consulta = f"SELECT id, nome, papel FROM usuarios WHERE nome = '{d.nome}' AND senha = '{d.senha}'"
    with conn() as c:
        try:
            linha = c.execute(consulta).fetchone()
        except psycopg.Error as erro:
            raise HTTPException(500, f"erro de banco: {erro}")     # ainda devolve o erro do banco ao cliente
    if linha is None:
        raise HTTPException(401, "credenciais invalidas")
    return {"token": jwt.encode({"sub": linha[1], "uid": linha[0], "papel": linha[2]}, SECRET, algorithm="HS256")}


@app.get("/entregas")
def listar(authorization: str = Header(default="")):
    usuario_do_token(authorization)
    with conn() as c:
        # [F4] devolve TODAS as entregas, de todos os motoristas; o filtro "só as minhas" fica no navegador
        linhas = c.execute("SELECT id, codigo, destinatario, cpf, endereco, motorista_id, status FROM entregas ORDER BY id").fetchall()
    return [dict(zip(["id", "codigo", "destinatario", "cpf", "endereco", "motorista_id", "status"], l)) for l in linhas]


@app.get("/entregas/{entrega_id}")
def obter(entrega_id: int, authorization: str = Header(default="")):
    usuario_do_token(authorization)
    with conn() as c:
        # [F5] não confere se a entrega é do usuário (IDOR)
        l = c.execute("SELECT id, codigo, destinatario, cpf, endereco, motorista_id, status FROM entregas WHERE id = %s", (entrega_id,)).fetchone()
    if l is None:
        raise HTTPException(404, "nao encontrada")
    return dict(zip(["id", "codigo", "destinatario", "cpf", "endereco", "motorista_id", "status"], l))


@app.post("/entregas/{entrega_id}/confirmar")
def confirmar(entrega_id: int, d: Confirmacao, authorization: str = Header(default="")):
    usuario_do_token(authorization)
    with conn() as c:
        # [F6] aceita qualquer coordenada informada pelo cliente; [F7] não registra quem confirmou, nem quando, nem de onde
        c.execute("UPDATE entregas SET status = 'entregue', conf_lat = %s, conf_lon = %s WHERE id = %s", (d.lat, d.lon, entrega_id))
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
def auditoria(entrega_id: int):
    raise HTTPException(404, "este sistema nao guarda trilha de auditoria")      # [F7]


@app.get("/", response_class=HTMLResponse)
def front():
    # [F4] a "autorização" está aqui: o navegador só mostra as entregas do motorista logado.
    return """<!doctype html><meta charset="utf-8"><title>LunaLog (inseguro)</title>
<h3>LunaLog: minhas entregas</h3>
<input id="n" placeholder="usuario"> <input id="s" type="password" placeholder="senha"> <button onclick="entrar()">Entrar</button>
<pre id="saida"></pre>
<script>
async function entrar() {
  const r = await fetch('/login', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                   body: JSON.stringify({nome: n.value, senha: s.value})});
  if (!r.ok) { saida.textContent = 'login recusado'; return; }
  const {token} = await r.json();
  const uid = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).uid;
  const todas = await (await fetch('/entregas', {headers: {Authorization: 'Bearer ' + token}})).json();
  const minhas = todas.filter(e => e.motorista_id === uid);      // o filtro só existe no navegador
  saida.textContent = JSON.stringify(minhas, null, 2);
}
</script>"""
