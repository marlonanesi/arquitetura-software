"""BRANCH BY ABSTRACTION: a abstração "Fonte de entregas" e as suas duas implementações.

Todo o serviço novo depende só de FonteDeEntregas. Hoje há duas implementações:
  FonteLegado    lê e grava no legado, passando pela ACL
  FontePropria   lê e grava no armazenamento do próprio serviço novo

A troca entre elas é uma FLAG (veja main.py). Quando a FontePropria tiver paridade comprovada e estiver
em produção, a FonteLegado (e a ACL) são REMOVIDAS: o resto do serviço não muda.
"""
from datetime import date
from typing import Protocol

import httpx

import acl
from dominio import Entrega, StatusEntrega, Transportadora


class FonteDeEntregas(Protocol):
    def obter(self, entrega_id: str) -> Entrega | None: ...

    def salvar(self, entrega: Entrega) -> None: ...


class FonteLegado:
    def __init__(self, url: str):
        self._url = url
        self._http = httpx.Client(timeout=5)

    def obter(self, entrega_id: str) -> Entrega | None:
        r = self._http.get(f"{self._url}/entregas/{entrega_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return acl.para_dominio(r.json())

    def salvar(self, entrega: Entrega) -> None:
        self._http.post(f"{self._url}/entregas", json=acl.para_legado(entrega)).raise_for_status()


class FontePropria:
    """O armazenamento do serviço novo. Aqui, em memória; em produção, o banco dedicado (lab 8D)."""

    def __init__(self):
        self._dados: dict[str, Entrega] = {}
        self._semear()

    def _semear(self) -> None:
        tr, vz, br = (Transportadora("transrapida", "TransRápida"), Transportadora("veloz", "Veloz Express"),
                      Transportadora("boreal", "Logística Boreal"))
        for e in (
            Entrega("E-1", StatusEntrega.ENTREGUE, date(2026, 11, 3), 11300, tr),
            Entrega("E-2", StatusEntrega.EM_ROTA, date(2026, 11, 4), 125050, vz),
            Entrega("E-3", StatusEntrega.AGUARDANDO_COLETA, date(2026, 11, 5), 8990, tr),
            Entrega("E-4", StatusEntrega.CANCELADA, date(2026, 11, 6), 4500, br),
            Entrega("E-5", StatusEntrega.EM_ROTA, date(2026, 11, 7), 30000, vz),
            Entrega("E-6", StatusEntrega.EM_ROTA, date(2026, 10, 1), 7000, tr),
        ):
            self._dados[e.id] = e

    def obter(self, entrega_id: str) -> Entrega | None:
        return self._dados.get(entrega_id)

    def salvar(self, entrega: Entrega) -> None:
        self._dados[entrega.id] = entrega
