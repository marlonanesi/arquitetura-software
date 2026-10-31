"""Os casos de uso orquestram o domínio por meio das portas."""
from confirmacao.dominio.entrega import Entrega, EntregaNaoEncontrada
from confirmacao.dominio.geo import Coordenada, distancia_metros
from confirmacao.dominio.portas import Geocodificador, Notificador, RepositorioEntregas, Relogio


class RegistrarEntrega:
    def __init__(self, repositorio: RepositorioEntregas):
        self._repositorio = repositorio

    def executar(self, entrega_id: str, endereco: str) -> Entrega:
        entrega = Entrega(id=entrega_id, endereco=endereco)
        self._repositorio.salvar(entrega)
        return entrega


class IniciarRota:
    def __init__(self, repositorio: RepositorioEntregas):
        self._repositorio = repositorio

    def executar(self, entrega_id: str) -> Entrega:
        entrega = self._repositorio.obter(entrega_id)
        if entrega is None:
            raise EntregaNaoEncontrada(entrega_id)
        entrega = entrega.iniciar_rota()
        self._repositorio.salvar(entrega)
        return entrega


class ConfirmarEntrega:
    def __init__(self, repositorio: RepositorioEntregas, geocodificador: Geocodificador,
                 notificador: Notificador, relogio: Relogio):
        self._repositorio = repositorio
        self._geocodificador = geocodificador
        self._notificador = notificador
        self._relogio = relogio

    def executar(self, entrega_id: str, posicao_do_motorista: Coordenada) -> Entrega:
        entrega = self._repositorio.obter(entrega_id)
        if entrega is None:
            raise EntregaNaoEncontrada(entrega_id)

        destino = self._geocodificador.coordenada_de(entrega.endereco)
        distancia = distancia_metros(posicao_do_motorista, destino)

        entrega = entrega.confirmar(distancia, self._relogio.agora())   # a regra de negócio mora aqui
        self._repositorio.salvar(entrega)
        self._notificador.entrega_confirmada(entrega)
        return entrega
