"""Geometria mínima do domínio: coordenadas e distância entre dois pontos."""
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt


@dataclass(frozen=True)
class Coordenada:
    lat: float
    lon: float


def distancia_metros(a: Coordenada, b: Coordenada) -> float:
    """Distância pela fórmula de haversine."""
    raio_terra = 6_371_000
    dlat = radians(b.lat - a.lat)
    dlon = radians(b.lon - a.lon)
    h = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlon / 2) ** 2
    return 2 * raio_terra * asin(sqrt(h))
