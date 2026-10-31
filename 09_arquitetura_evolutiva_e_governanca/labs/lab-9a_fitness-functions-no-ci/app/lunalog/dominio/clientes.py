"""Domínio de clientes: cadastro. Não conhece tarifas nem a API."""
from lunalog.infra import repositorio


def buscar_cliente(cliente_id: str) -> dict | None:
    return repositorio.cliente_por_id(cliente_id)
