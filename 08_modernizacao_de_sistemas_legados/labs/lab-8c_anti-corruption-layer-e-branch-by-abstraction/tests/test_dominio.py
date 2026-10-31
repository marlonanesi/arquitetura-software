"""Testes do domínio: nenhum deles menciona o legado, e nenhum precisa de rede."""
from datetime import date

from dominio import Entrega, StatusEntrega, Transportadora

T = Transportadora("veloz", "Veloz Express")
HOJE = date(2026, 11, 2)


def test_em_rota_depois_da_previsao_esta_atrasada():
    assert Entrega("E-1", StatusEntrega.EM_ROTA, date(2026, 10, 1), 100, T).atrasada(HOJE)


def test_em_rota_antes_da_previsao_nao_esta_atrasada():
    assert not Entrega("E-1", StatusEntrega.EM_ROTA, date(2026, 11, 5), 100, T).atrasada(HOJE)


def test_entregue_nunca_esta_atrasada():
    assert not Entrega("E-1", StatusEntrega.ENTREGUE, date(2026, 10, 1), 100, T).atrasada(HOJE)
