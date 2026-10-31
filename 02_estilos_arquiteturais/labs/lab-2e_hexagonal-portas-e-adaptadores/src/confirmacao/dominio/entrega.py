"""A entidade Entrega e as regras de negócio da confirmação.

Nada aqui conhece banco, rede ou framework: só regras e dados.
"""
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

RAIO_CONFIRMACAO_METROS = 100


class Status(str, Enum):
    CRIADA = "criada"
    EM_ROTA = "em_rota"
    ENTREGUE = "entregue"


class ErroDeDominio(Exception):
    """Base dos erros que representam uma regra de negócio violada."""


class EntregaNaoEncontrada(ErroDeDominio):
    pass


class EntregaNaoEstaEmRota(ErroDeDominio):
    pass


class ForaDoRaioDeConfirmacao(ErroDeDominio):
    pass


@dataclass(frozen=True)
class Entrega:
    id: str
    endereco: str
    status: Status = Status.CRIADA
    confirmada_em: datetime | None = None

    def iniciar_rota(self) -> "Entrega":
        if self.status != Status.CRIADA:
            raise ErroDeDominio(f"entrega {self.id} nao pode iniciar rota no status {self.status.value}")
        return replace(self, status=Status.EM_ROTA)

    def confirmar(self, distancia_ao_destino_m: float, agora: datetime) -> "Entrega":
        """Regra: só se confirma uma entrega em rota, a até 100 m do endereço."""
        if self.status != Status.EM_ROTA:
            raise EntregaNaoEstaEmRota(f"entrega {self.id} esta {self.status.value}, nao em rota")
        if distancia_ao_destino_m > RAIO_CONFIRMACAO_METROS:
            raise ForaDoRaioDeConfirmacao(
                f"motorista a {distancia_ao_destino_m:.0f} m do destino (maximo {RAIO_CONFIRMACAO_METROS} m)"
            )
        return replace(self, status=Status.ENTREGUE, confirmada_em=agora)
