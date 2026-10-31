"""Adaptador de notificação que escreve uma linha no log (padrão do lab)."""
import json

from confirmacao.dominio.entrega import Entrega


class NotificadorEmLog:
    def entrega_confirmada(self, entrega: Entrega) -> None:
        print("NOTIFICACAO " + json.dumps({"evento": "EntregaConfirmada", "entrega": entrega.id,
                                          "confirmada_em": entrega.confirmada_em.isoformat()}))
