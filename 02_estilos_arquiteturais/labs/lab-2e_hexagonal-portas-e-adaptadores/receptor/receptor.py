"""Receptor de webhook de brincadeira: imprime o corpo de cada POST que recebe."""
from http.server import BaseHTTPRequestHandler, HTTPServer


class Receptor(BaseHTTPRequestHandler):
    def do_POST(self):
        corpo = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
        print(f"WEBHOOK RECEBIDO: {corpo}", flush=True)
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


print("receptor de webhook na porta 9000", flush=True)
HTTPServer(("0.0.0.0", 9000), Receptor).serve_forever()
