"""Adaptador de repositório em memória: ideal para testes e para a primeira versão."""
from confirmacao.dominio.entrega import Entrega


class RepositorioEmMemoria:
    def __init__(self):
        self._entregas: dict[str, Entrega] = {}

    def salvar(self, entrega: Entrega) -> None:
        self._entregas[entrega.id] = entrega

    def obter(self, entrega_id: str) -> Entrega | None:
        return self._entregas.get(entrega_id)
