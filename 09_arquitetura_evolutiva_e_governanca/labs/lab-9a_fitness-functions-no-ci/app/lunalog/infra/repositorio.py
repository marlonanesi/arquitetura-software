"""Camada de infraestrutura: de onde vêm os dados. Aqui, tabelas em memória."""

TARIFA_POR_REGIAO = {"sudeste": 0.9, "sul": 1.0, "nordeste": 1.3}

CLIENTES = {
    "C-1": {"id": "C-1", "nome": "Transportes Aurora"},
    "C-2": {"id": "C-2", "nome": "Logistica Boreal"},
}


def tarifa_da_regiao(regiao: str) -> float:
    return TARIFA_POR_REGIAO.get(regiao, 1.0)


def cliente_por_id(cliente_id: str) -> dict | None:
    return CLIENTES.get(cliente_id)
