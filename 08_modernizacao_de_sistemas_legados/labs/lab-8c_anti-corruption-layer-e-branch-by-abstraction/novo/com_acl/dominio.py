"""O modelo de domínio do serviço NOVO: limpo, sem nenhum traço do legado.

Nomes claros, status como tipo próprio, data como data, dinheiro em centavos (inteiro), transportadora
como objeto. Nada aqui sabe que o legado existe.
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum

HOJE_DO_LAB = date(2026, 11, 2)      # fixo, para o lab ter resultados repetíveis


class StatusEntrega(str, Enum):
    AGUARDANDO_COLETA = "aguardando_coleta"
    EM_ROTA = "em_rota"
    ENTREGUE = "entregue"
    CANCELADA = "cancelada"


@dataclass(frozen=True)
class Transportadora:
    id: str
    nome: str


@dataclass(frozen=True)
class Entrega:
    id: str
    status: StatusEntrega
    previsao: date
    valor_centavos: int
    transportadora: Transportadora

    def atrasada(self, hoje: date = HOJE_DO_LAB) -> bool:
        """Regra de negócio: está atrasada a entrega que ainda está em rota depois da previsão."""
        return self.status == StatusEntrega.EM_ROTA and self.previsao < hoje
