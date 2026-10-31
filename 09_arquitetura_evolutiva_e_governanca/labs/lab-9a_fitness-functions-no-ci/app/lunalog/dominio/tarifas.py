"""Domínio de tarifas: calcula o frete. Não conhece clientes nem a API."""
from lunalog.infra import repositorio


def calcular_frete(peso_kg: float, distancia_km: float, regiao: str) -> float:
    if peso_kg <= 0 or distancia_km <= 0:
        raise ValueError("peso e distancia devem ser positivos")
    return round(8.0 + peso_kg * 1.5 + distancia_km * repositorio.tarifa_da_regiao(regiao), 2)
