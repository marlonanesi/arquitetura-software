"""API pública do módulo de notificação."""
from app.notificacao import canais, repositorio


def avisar_destinatario(conn, entrega_id: int, canal: str) -> None:
    canais.enviar(canal, entrega_id)
    repositorio.registrar(conn, entrega_id, canal)


def definir_falha(ligada: bool) -> None:
    canais.estado["falha"] = ligada
