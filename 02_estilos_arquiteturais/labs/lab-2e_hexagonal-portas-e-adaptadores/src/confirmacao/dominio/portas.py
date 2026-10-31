"""As PORTAS: o que o domínio precisa do mundo exterior, descrito como contratos.

O domínio define as interfaces; a infraestrutura (os adaptadores) é que se adapta a elas.
É a inversão de dependência: a seta aponta para o domínio.
"""
from datetime import datetime
from typing import Protocol

from confirmacao.dominio.entrega import Entrega
from confirmacao.dominio.geo import Coordenada


class RepositorioEntregas(Protocol):
    def salvar(self, entrega: Entrega) -> None: ...

    def obter(self, entrega_id: str) -> Entrega | None: ...


class Geocodificador(Protocol):
    def coordenada_de(self, endereco: str) -> Coordenada: ...


class Notificador(Protocol):
    def entrega_confirmada(self, entrega: Entrega) -> None: ...


class Relogio(Protocol):
    def agora(self) -> datetime: ...
