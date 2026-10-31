"""Simula os destinos das notificações do Alertmanager (plantão, fila de tickets e canal de ruído).
Só imprime, de forma legível, cada notificação recebida."""
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

DESTINOS = {
    "/plantao": "PLANTAO (acorda alguem)",
    "/tickets": "TICKET (proximo dia util)",
    "/ruido": "RUIDO (alerta por causa)",
}


class Receptor(BaseHTTPRequestHandler):
    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        destino = DESTINOS.get(self.path, self.path)
        for alerta in corpo.get("alerts", []):
            rotulos = alerta.get("labels", {})
            extra = f" servico={rotulos['job']}" if "job" in rotulos else ""
            resumo = alerta.get("annotations", {}).get("resumo", "")
            print(f"{datetime.now():%H:%M:%S} [{destino}] {alerta['status'].upper()} {rotulos.get('alertname')}{extra} - {resumo}", flush=True)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print("receptor de notificacoes pronto na porta 9000", flush=True)
    HTTPServer(("0.0.0.0", 9000), Receptor).serve_forever()
