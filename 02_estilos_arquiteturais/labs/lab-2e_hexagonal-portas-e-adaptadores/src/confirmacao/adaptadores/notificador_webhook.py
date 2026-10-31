"""Adaptador de notificação que envia um webhook HTTP (só biblioteca padrão)."""
import json
import urllib.request

from confirmacao.dominio.entrega import Entrega


class NotificadorWebhook:
    def __init__(self, url: str):
        self._url = url

    def entrega_confirmada(self, entrega: Entrega) -> None:
        corpo = json.dumps({"evento": "EntregaConfirmada", "entrega": entrega.id,
                            "confirmada_em": entrega.confirmada_em.isoformat()}).encode()
        pedido = urllib.request.Request(self._url, data=corpo, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=3) as resposta:
            print(f"NOTIFICACAO enviada por webhook para {self._url} (http {resposta.status})")
