"""Teste de CONTRATO: a mesma bateria roda contra cada adaptador de repositório.

Se um adaptador novo passa nesta bateria, ele pode substituir os outros sem o domínio perceber.
O PostgreSQL só entra se a variável POSTGRES_URL estiver definida.
"""
import os
import uuid
from datetime import datetime, timezone

import pytest

from confirmacao.adaptadores.repositorio_memoria import RepositorioEmMemoria
from confirmacao.adaptadores.repositorio_sqlite import RepositorioSqlite
from confirmacao.dominio.entrega import Entrega, Status


def _postgres():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        pytest.skip("defina POSTGRES_URL para testar o adaptador PostgreSQL")
    from confirmacao.adaptadores.repositorio_postgres import RepositorioPostgres
    return RepositorioPostgres(url)


@pytest.fixture(params=["memoria", "sqlite", "postgres"])
def repositorio(request, tmp_path):
    if request.param == "memoria":
        return RepositorioEmMemoria()
    if request.param == "sqlite":
        return RepositorioSqlite(str(tmp_path / "teste.db"))
    return _postgres()


def novo_id() -> str:
    return "T-" + uuid.uuid4().hex[:8]


def test_obter_inexistente_devolve_none(repositorio):
    assert repositorio.obter(novo_id()) is None


def test_salvar_e_obter(repositorio):
    entrega = Entrega(id=novo_id(), endereco="Av. Paulista, 1000")
    repositorio.salvar(entrega)
    assert repositorio.obter(entrega.id) == entrega


def test_salvar_de_novo_atualiza(repositorio):
    entrega = Entrega(id=novo_id(), endereco="Av. Paulista, 1000")
    repositorio.salvar(entrega)
    atualizada = entrega.iniciar_rota()
    repositorio.salvar(atualizada)
    assert repositorio.obter(entrega.id).status == Status.EM_ROTA


def test_preserva_a_data_de_confirmacao(repositorio):
    quando = datetime(2026, 10, 27, 14, 0, tzinfo=timezone.utc)
    entrega = Entrega(id=novo_id(), endereco="x", status=Status.ENTREGUE, confirmada_em=quando)
    repositorio.salvar(entrega)
    assert repositorio.obter(entrega.id).confirmada_em == quando
