"""Testes do domínio com Event Sourcing: dado um histórico de eventos, o comando devolve os novos eventos (ou recusa)."""
import pytest

from dominio import Entrega, ErroDeDominio, atualizar_esquema

DESTINO = (-23.5614, -46.6559)


def historico(*comandos):
    """Monta o estado a partir de comandos válidos, aplicando os eventos que eles geram."""
    e = Entrega("E-1")
    for c in comandos:
        for ev in c(e):
            e.aplicar(ev)
    return e


registrar = lambda e: e.registrar("E-1001", "rapido", "2026-11-10", *DESTINO, "ana")
iniciar = lambda e: e.iniciar_rota("bruno", "ana")


def test_registrar_gera_um_evento_e_o_estado_nasce_dele():
    e = historico(registrar)
    assert (e.status, e.versao, e.transportadora) == ("criada", 1, "rapido")


def test_nao_se_registra_duas_vezes():
    with pytest.raises(ErroDeDominio):
        historico(registrar).registrar("E-1001", "rapido", "2026-11-10", *DESTINO, "ana")


def test_confirmar_perto_do_destino():
    e = historico(registrar, iniciar)
    eventos = e.confirmar(*DESTINO, "bruno")
    assert [x["tipo"] for x in eventos] == ["EntregaConfirmada"]
    assert eventos[0]["dados"]["distancia_m"] == 0


def test_confirmar_longe_e_recusado_e_nao_gera_evento():
    e = historico(registrar, iniciar)
    with pytest.raises(ErroDeDominio):
        e.confirmar(DESTINO[0] + 0.02, DESTINO[1], "bruno")
    assert e.versao == 2            # nada foi acrescentado


def test_nao_se_confirma_o_que_nao_saiu_para_a_rota():
    with pytest.raises(ErroDeDominio):
        historico(registrar).confirmar(*DESTINO, "bruno")


def test_entrega_entregue_nao_pode_ser_cancelada():
    e = historico(registrar, iniciar, lambda e: e.confirmar(*DESTINO, "bruno"))
    with pytest.raises(ErroDeDominio):
        e.cancelar("desistencia", "ana")


def test_replay_e_determinista():
    e1 = historico(registrar, iniciar, lambda e: e.reagendar("2026-11-12", "chuva", "ana"))
    refeito = Entrega.reconstruir("E-1", [{"tipo": "EntregaRegistrada", "esquema": 1,
                                           "dados": {"codigo": "E-1001", "transportadora": "rapido", "previsao": "2026-11-10", "lat": DESTINO[0], "lon": DESTINO[1]}, "ator": "ana"},
                                          {"tipo": "RotaIniciada", "esquema": 1, "dados": {"motorista": "bruno"}, "ator": "ana"},
                                          {"tipo": "EntregaReagendada", "esquema": 2, "dados": {"nova_previsao": "2026-11-12", "motivo": "chuva"}, "ator": "ana"}])
    assert (refeito.status, refeito.previsao, refeito.reagendamentos, refeito.versao) == (e1.status, e1.previsao, e1.reagendamentos, e1.versao)


def test_upcasting_le_o_evento_antigo_no_formato_novo():
    antigo = {"tipo": "EntregaReagendada", "esquema": 1, "dados": {"nova_previsao": "2026-12-20"}, "ator": "legado"}
    novo = atualizar_esquema(antigo)
    assert novo["esquema"] == 2 and novo["dados"]["motivo"] == "nao_informado"
    assert antigo["esquema"] == 1       # o evento original NAO foi alterado
