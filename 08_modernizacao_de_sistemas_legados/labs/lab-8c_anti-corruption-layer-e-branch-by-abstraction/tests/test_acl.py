"""Testes da ACL: a tradução entre o modelo do legado e o domínio, nos dois sentidos."""
from datetime import date

import pytest

import acl
from dominio import StatusEntrega


def legado(**mudancas):
    base = {"COD_ENT": "E-9", "ST": 2, "DT_PREV": "04/11/2026", "VLR": "1.250,50", "TRANSP": "VELOZ EXPRESS S/A"}
    return {**base, **mudancas}


def test_traduz_o_formato_antigo_para_o_dominio():
    e = acl.para_dominio(legado())
    assert (e.id, e.status, e.previsao, e.valor_centavos) == ("E-9", StatusEntrega.EM_ROTA, date(2026, 11, 4), 125050)
    assert (e.transportadora.id, e.transportadora.nome) == ("veloz", "Veloz Express")


@pytest.mark.parametrize("st, esperado", [(1, "aguardando_coleta"), (2, "em_rota"), ("2", "em_rota"), (3, "entregue"),
                                          (9, "cancelada"), ("EM_ROTA", "em_rota"), ("entregue", "entregue")])
def test_status_numerico_texto_numerico_ou_nome(st, esperado):
    assert acl.para_dominio(legado(ST=st)).status.value == esperado


@pytest.mark.parametrize("data", ["04/11/2026", "2026-11-04"])
def test_as_duas_datas_do_legado(data):
    assert acl.para_dominio(legado(DT_PREV=data)).previsao == date(2026, 11, 4)


@pytest.mark.parametrize("vlr, centavos", [("113,00", 11300), ("1.250,50", 125050), ("89.9", 8990), (45, 4500), ("1250.50", 125050)])
def test_valores_com_virgula_ponto_ou_numero(vlr, centavos):
    assert acl.para_dominio(legado(VLR=vlr)).valor_centavos == centavos


@pytest.mark.parametrize("campo, valor", [("ST", 7), ("DT_PREV", "ontem"), ("VLR", "muito"), ("TRANSP", "OUTRA LTDA")])
def test_o_que_nao_sabe_traduzir_falha_de_forma_clara(campo, valor):
    with pytest.raises(acl.ErroDeTraducao):
        acl.para_dominio(legado(**{campo: valor}))


def test_campo_ausente_falha_de_forma_clara():
    incompleto = legado()
    del incompleto["VLR"]
    with pytest.raises(acl.ErroDeTraducao):
        acl.para_dominio(incompleto)


def test_ida_e_volta_nao_perde_nada():
    original = acl.para_dominio(legado())
    assert acl.para_dominio(acl.para_legado(original)) == original


def test_escreve_no_formato_que_o_legado_entende():
    escrito = acl.para_legado(acl.para_dominio(legado(VLR="89.9", DT_PREV="2026-11-05", ST="1")))
    assert escrito == {"COD_ENT": "E-9", "ST": 1, "DT_PREV": "05/11/2026", "VLR": "89,90", "TRANSP": "VELOZ EXPRESS S/A"}
