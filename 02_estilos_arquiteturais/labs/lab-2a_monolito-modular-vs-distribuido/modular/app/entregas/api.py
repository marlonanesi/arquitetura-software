"""API pública do módulo de entregas. É a única porta de entrada para os outros módulos."""
from app.entregas import repositorio, servico


def registrar_entrega(conn, codigo: str, destino: str) -> dict:
    return servico.registrar(conn, codigo, destino)


def obter_entrega(conn, entrega_id: int):
    return repositorio.obter(conn, entrega_id)
