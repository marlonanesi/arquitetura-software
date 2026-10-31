"""API pública do módulo de roteirização."""
from app.roteirizacao import calculo, repositorio


def atribuir_rota(conn, entrega_id: int, destino: str) -> dict:
    rota = calculo.calcular(destino)
    repositorio.inserir_rota(conn, entrega_id, rota["sequencia"], rota["motorista"])
    return rota
