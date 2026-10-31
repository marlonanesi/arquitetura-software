"""Testes de CONTRATO da abstração: a mesma bateria contra as duas implementações.

A FonteLegado precisa do legado no ar (LEGADO_URL). O teste de paridade confirma que a FontePropria
devolve EXATAMENTE as mesmas entregas que o legado, já traduzidas: é a prova para trocar a flag.
"""
import os
import uuid
from datetime import date

import httpx
import pytest

from dominio import Entrega, StatusEntrega, Transportadora
from fonte import FonteLegado, FontePropria

LEGADO_URL = os.environ.get("LEGADO_URL", "http://legado:8000")
IDS = ["E-1", "E-2", "E-3", "E-4", "E-5", "E-6"]


@pytest.fixture(params=["legado", "proprio"])
def fonte(request):
    return FonteLegado(LEGADO_URL) if request.param == "legado" else FontePropria()


def test_entrega_inexistente_devolve_none(fonte):
    assert fonte.obter("E-9999") is None


def test_salvar_e_obter(fonte):
    nova = Entrega("E-" + str(uuid.uuid4().int)[:6], StatusEntrega.EM_ROTA, date(2026, 12, 1), 12345,
                   Transportadora("boreal", "Logística Boreal"))
    fonte.salvar(nova)
    assert fonte.obter(nova.id) == nova


@pytest.mark.parametrize("entrega_id", IDS)
def test_paridade_entre_o_legado_e_a_fonte_propria(entrega_id):
    assert FonteLegado(LEGADO_URL).obter(entrega_id) == FontePropria().obter(entrega_id)


def test_paridade_continua_quando_o_legado_muda_de_formato():
    httpx.post(f"{LEGADO_URL}/admin/formato", params={"modo": "novo"})
    try:
        for entrega_id in IDS:
            assert FonteLegado(LEGADO_URL).obter(entrega_id) == FontePropria().obter(entrega_id)
    finally:
        httpx.post(f"{LEGADO_URL}/admin/formato", params={"modo": "antigo"})
