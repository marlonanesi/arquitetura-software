"""Dublês de teste: implementações mínimas das portas, escritas à mão (sem biblioteca de mocks)."""
from datetime import datetime, timezone

from confirmacao.dominio.entrega import Entrega
from confirmacao.dominio.geo import Coordenada

DESTINO = Coordenada(-23.5614, -46.6559)
AGORA = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)


class GeocodificadorFixo:
    def coordenada_de(self, endereco: str) -> Coordenada:
        return DESTINO


class RelogioFixo:
    def agora(self) -> datetime:
        return AGORA


class NotificadorEspiao:
    def __init__(self):
        self.enviadas: list[Entrega] = []

    def entrega_confirmada(self, entrega: Entrega) -> None:
        self.enviadas.append(entrega)
