"""Envio da mensagem pelo canal escolhido (simulado)."""

# Interruptor de falha, para o experimento "o canal de notificação está fora".
estado = {"falha": False}


def enviar(canal: str, entrega_id: int) -> None:
    if estado["falha"]:
        raise RuntimeError(f"canal {canal} indisponivel")
