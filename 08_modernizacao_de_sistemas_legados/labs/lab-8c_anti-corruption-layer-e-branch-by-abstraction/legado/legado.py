"""O monólito legado da LunaLog (versão 2021), o mesmo estilo do lab 8B, com mais casos de formatos antigos.

Modelo antigo, de propósito:
  COD_ENT   código da entrega
  ST        status NUMÉRICO (1 aguardando coleta, 2 em rota, 3 entregue, 9 cancelada), às vezes como texto
  DT_PREV   previsão em dd/mm/aaaa, às vezes em aaaa-mm-dd (vários times, vários formatos)
  VLR       valor com vírgula decimal ("1.250,50"), com ponto ("89.9") ou até como número
  TRANSP    nome da transportadora em maiúsculas, com sufixo societário

Interruptor para o lab: POST /admin/formato?modo=novo faz o legado passar a devolver status em texto,
data ISO e valor com ponto: uma "mudança no legado" que o sistema novo precisa absorver.
"""
import json
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

# Os dados exatamente como o legado os guarda (e devolve no modo "antigo")
DADOS = {
    "E-1": {"ST": 3, "DT_PREV": "03/11/2026", "VLR": "113,00", "TRANSP": "TRANSRAPIDA LTDA"},
    "E-2": {"ST": 2, "DT_PREV": "04/11/2026", "VLR": "1.250,50", "TRANSP": "VELOZ EXPRESS S/A"},
    "E-3": {"ST": 1, "DT_PREV": "2026-11-05", "VLR": "89.9", "TRANSP": "TRANSRAPIDA LTDA"},
    "E-4": {"ST": 9, "DT_PREV": "06/11/2026", "VLR": 45, "TRANSP": "LOG BOREAL ME"},
    "E-5": {"ST": "2", "DT_PREV": "07/11/2026", "VLR": "300,00", "TRANSP": "VELOZ EXPRESS S/A"},
    "E-6": {"ST": 2, "DT_PREV": "01/10/2026", "VLR": "70,00", "TRANSP": "TRANSRAPIDA LTDA"},
}
TEXTO_STATUS = {1: "AGUARDANDO_COLETA", 2: "EM_ROTA", 3: "ENTREGUE", 9: "CANCELADA"}
estado = {"modo": "antigo", "ultima_escrita": None}


def data_iso(texto: str) -> str:
    return datetime.strptime(texto, "%d/%m/%Y").date().isoformat() if "/" in texto else texto


def valor_ponto(v) -> str:
    texto = str(v)
    return texto.replace(".", "").replace(",", ".") if "," in texto else texto


def apresentar(cod: str) -> dict:
    d = DADOS[cod]
    if estado["modo"] == "antigo":
        return {"COD_ENT": cod, **d}
    # modo "novo": o legado passou a devolver status em texto, data ISO e valor com ponto
    return {"COD_ENT": cod, "ST": TEXTO_STATUS[int(d["ST"])], "DT_PREV": data_iso(d["DT_PREV"]),
            "VLR": valor_ponto(d["VLR"]), "TRANSP": d["TRANSP"]}


class H(BaseHTTPRequestHandler):
    def responder(self, corpo, status=200):
        dados = json.dumps(corpo, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urlparse(self.path)
        m = re.fullmatch(r"/entregas/(E-\d+)", url.path)
        if m:
            if m.group(1) not in DADOS:
                return self.responder({"erro": "nao encontrada"}, 404)
            print(f"legado atendeu GET {url.path}", flush=True)
            return self.responder(apresentar(m.group(1)))
        if url.path == "/ultima-escrita":
            return self.responder(estado["ultima_escrita"] or {})
        if url.path == "/admin/formato":
            return self.responder({"modo": estado["modo"]})
        self.responder({"erro": "rota inexistente"}, 404)

    def do_POST(self):
        url = urlparse(self.path)
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        if url.path == "/admin/formato":
            modo = parse_qs(url.query).get("modo", ["antigo"])[0]
            estado["modo"] = modo
            return self.responder({"modo": modo})
        if url.path == "/entregas":
            # o legado só aceita o próprio formato
            DADOS[corpo["COD_ENT"]] = {k: corpo[k] for k in ("ST", "DT_PREV", "VLR", "TRANSP")}
            estado["ultima_escrita"] = corpo
            print(f"legado recebeu POST /entregas: {corpo}", flush=True)
            return self.responder({"ok": True}, 201)
        self.responder({"erro": "rota inexistente"}, 404)

    def log_message(self, *args):
        pass


print("legado na porta 8000", flush=True)
ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
