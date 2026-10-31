"""Testes do DOMÍNIO: rodam em milissegundos, sem banco, sem rede, sem fila.

Usam adaptadores em memória e dublês fixos. É o que a arquitetura hexagonal torna possível.
"""
import pytest
from doubles import AGORA, DESTINO, GeocodificadorFixo, NotificadorEspiao, RelogioFixo

from confirmacao.adaptadores.repositorio_memoria import RepositorioEmMemoria
from confirmacao.dominio.casos_de_uso import ConfirmarEntrega, IniciarRota, RegistrarEntrega
from confirmacao.dominio.entrega import (EntregaNaoEncontrada, EntregaNaoEstaEmRota,
                                         ForaDoRaioDeConfirmacao, Status)
from confirmacao.dominio.geo import Coordenada


@pytest.fixture
def cenario():
    repo = RepositorioEmMemoria()
    notificador = NotificadorEspiao()
    return {
        "repo": repo,
        "notificador": notificador,
        "registrar": RegistrarEntrega(repo),
        "iniciar": IniciarRota(repo),
        "confirmar": ConfirmarEntrega(repo, GeocodificadorFixo(), notificador, RelogioFixo()),
    }


def entrega_em_rota(c):
    c["registrar"].executar("E-1", "Rua das Flores, 100")
    c["iniciar"].executar("E-1")


def test_confirma_no_endereco_e_notifica(cenario):
    entrega_em_rota(cenario)
    entrega = cenario["confirmar"].executar("E-1", DESTINO)
    assert entrega.status == Status.ENTREGUE
    assert entrega.confirmada_em == AGORA
    assert [e.id for e in cenario["notificador"].enviadas] == ["E-1"]


def test_recusa_confirmacao_longe_do_destino(cenario):
    entrega_em_rota(cenario)
    longe = Coordenada(DESTINO.lat + 0.02, DESTINO.lon)   # cerca de 2 km
    with pytest.raises(ForaDoRaioDeConfirmacao):
        cenario["confirmar"].executar("E-1", longe)
    assert cenario["repo"].obter("E-1").status == Status.EM_ROTA
    assert cenario["notificador"].enviadas == []


def test_recusa_confirmar_entrega_que_nao_saiu_para_entrega(cenario):
    cenario["registrar"].executar("E-1", "Rua das Flores, 100")
    with pytest.raises(EntregaNaoEstaEmRota):
        cenario["confirmar"].executar("E-1", DESTINO)


def test_nao_confirma_duas_vezes(cenario):
    entrega_em_rota(cenario)
    cenario["confirmar"].executar("E-1", DESTINO)
    with pytest.raises(EntregaNaoEstaEmRota):
        cenario["confirmar"].executar("E-1", DESTINO)
    assert len(cenario["notificador"].enviadas) == 1


def test_entrega_inexistente(cenario):
    with pytest.raises(EntregaNaoEncontrada):
        cenario["confirmar"].executar("nao-existe", DESTINO)
