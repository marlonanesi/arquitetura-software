"""O serviço novo da LunaLog: assume, aos poucos, as rotas do legado.

Implementa /cotacao, /clientes e /relatorios com o mesmo contrato do legado (para o cliente
não perceber a troca). Ainda NÃO implementa /entregas: o modelo dela é o assunto do lab 8C.
"""
import json
import re
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

chamadas = Counter()
CLIENTES = {"C-1": ("Transportes Aurora", "contato@aurora.example"), "C-2": ("Logística Boreal", "ops@boreal.example")}


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
        consulta = {k: v[0] for k, v in parse_qs(url.query).items()}
        sombra = self.headers.get("X-Sombra") == "1"
        rota = "/" + url.path.strip("/").split("/")[0]
        if rota != "/estatisticas":
            chamadas[rota + (" (sombra)" if sombra else "")] += 1
            print(f"novo atendeu GET {url.path}" + (" [SOMBRA: cópia do tráfego, resposta descartada]" if sombra else ""), flush=True)

        if url.path == "/cotacao":
            peso, km = float(consulta.get("peso_kg", 1)), float(consulta.get("distancia_km", 1))
            return self.responder({"servico": "novo", "frete": round(8.0 + peso * 1.5 + km * 0.9, 2)})

        m = re.fullmatch(r"/clientes/(C-\d+)", url.path)
        if m:
            nome, email = CLIENTES.get(m.group(1), ("Desconhecido", ""))
            return self.responder({"servico": "novo", "id": m.group(1), "nome": nome, "email": email})

        if url.path == "/relatorios/mensal":
            return self.responder({"servico": "novo", "mes": "2026-10", "entregas": 1250, "no_prazo": 1187})

        if url.path == "/estatisticas":
            return self.responder(dict(chamadas))

        self.responder({"erro": "rota ainda nao migrada para o servico novo"}, 404)

    def log_message(self, *args):
        pass


print("servico novo na porta 8000", flush=True)
ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
