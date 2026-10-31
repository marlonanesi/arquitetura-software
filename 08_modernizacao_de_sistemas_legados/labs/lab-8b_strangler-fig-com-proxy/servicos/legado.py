"""O monólito legado da LunaLog (versão 2021): cotação, clientes, entregas e relatórios em um só lugar.

Atende tudo, tem formatos antigos (veja /entregas) e conta quantas chamadas recebeu por rota
(/estatisticas), o que permite medir o avanço da migração: quando uma rota para de receber
chamadas, ela já foi estrangulada.
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
        rota = "/" + url.path.strip("/").split("/")[0]
        if rota != "/estatisticas":
            chamadas[rota] += 1
            print(f"legado atendeu GET {url.path}", flush=True)

        if url.path == "/cotacao":
            peso, km = float(consulta.get("peso_kg", 1)), float(consulta.get("distancia_km", 1))
            return self.responder({"servico": "legado", "frete": round(8.0 + peso * 1.5 + km * 0.9, 2)})

        m = re.fullmatch(r"/clientes/(C-\d+)", url.path)
        if m:
            nome, email = CLIENTES.get(m.group(1), ("Desconhecido", ""))
            return self.responder({"servico": "legado", "id": m.group(1), "nome": nome, "email": email})

        # Modelo antigo, de propósito: nomes crípticos, status numérico, data em dd/mm/aaaa, valor com vírgula.
        # O lab 8C trata de como o sistema novo se protege desse modelo.
        m = re.fullmatch(r"/entregas/(E-\d+)", url.path)
        if m:
            return self.responder({"servico": "legado", "COD_ENT": m.group(1), "ST": 3, "DT_PREV": "03/11/2026",
                                   "VLR": "113,00", "TRANSP": "TRANSRAPIDA LTDA"})

        if url.path == "/relatorios/mensal":
            return self.responder({"servico": "legado", "mes": "2026-10", "entregas": 1250, "no_prazo": 1187})

        if url.path == "/estatisticas":
            return self.responder(dict(chamadas))

        self.responder({"erro": "rota inexistente"}, 404)

    def log_message(self, *args):
        pass


print("legado (monolito) na porta 8000", flush=True)
ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
