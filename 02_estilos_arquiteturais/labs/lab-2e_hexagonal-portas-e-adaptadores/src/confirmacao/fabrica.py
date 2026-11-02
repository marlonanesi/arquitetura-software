"""A RAIZ DE COMPOSIÇÃO: o único lugar que conhece domínio E adaptadores ao mesmo tempo.

Escolhe os adaptadores pelas variáveis de ambiente e os conecta às portas dos casos de uso.
Trocar um adaptador é mudar uma variável (ou, para um adaptador novo, registrá-lo aqui).

  REPOSITORIO     memoria | sqlite | postgres      (padrão: memoria)
  NOTIFICADOR     log | webhook                    (padrão: log)
  GEOCODIFICADOR  google | here                    (padrão: google)
"""
import os

from confirmacao.adaptadores.geocodificador_google import GeocodificadorGoogle
from confirmacao.adaptadores.geocodificador_here import GeocodificadorHere
from confirmacao.adaptadores.geocodificador_osm import GeocodificadorOsm
from confirmacao.adaptadores.notificador_log import NotificadorEmLog
from confirmacao.adaptadores.notificador_webhook import NotificadorWebhook
from confirmacao.adaptadores.relogio_sistema import RelogioDoSistema
from confirmacao.adaptadores.repositorio_memoria import RepositorioEmMemoria
from confirmacao.adaptadores.repositorio_postgres import RepositorioPostgres
from confirmacao.adaptadores.repositorio_sqlite import RepositorioSqlite
from confirmacao.dominio.casos_de_uso import ConfirmarEntrega, IniciarRota, RegistrarEntrega

REPOSITORIOS = {
    "memoria": lambda env: RepositorioEmMemoria(),
    "sqlite": lambda env: RepositorioSqlite(env.get("SQLITE_PATH", "entregas.db")),
    "postgres": lambda env: RepositorioPostgres(env["POSTGRES_URL"]),
}
NOTIFICADORES = {
    "log": lambda env: NotificadorEmLog(),
    "webhook": lambda env: NotificadorWebhook(env["WEBHOOK_URL"]),
}
GEOCODIFICADORES = {
    "google": lambda env: GeocodificadorGoogle(),
    "here": lambda env: GeocodificadorHere(),
    "osm": lambda env: GeocodificadorOsm(),

}


def _escolher(catalogo: dict, variavel: str, padrao: str, env):
    nome = env.get(variavel, padrao)
    if nome not in catalogo:
        raise SystemExit(f"{variavel}={nome!r} invalido. Opcoes: {', '.join(sorted(catalogo))}")
    return catalogo[nome](env)


def montar(env=os.environ) -> dict:
    repositorio = _escolher(REPOSITORIOS, "REPOSITORIO", "memoria", env)
    notificador = _escolher(NOTIFICADORES, "NOTIFICADOR", "log", env)
    geocodificador = _escolher(GEOCODIFICADORES, "GEOCODIFICADOR", "google", env)
    return {
        "registrar": RegistrarEntrega(repositorio),
        "iniciar_rota": IniciarRota(repositorio),
        "confirmar": ConfirmarEntrega(repositorio, geocodificador, notificador, RelogioDoSistema()),
        "repositorio": repositorio,
    }
