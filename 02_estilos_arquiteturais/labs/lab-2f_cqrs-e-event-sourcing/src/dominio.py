"""O domínio de entregas com Event Sourcing (evolução do domínio do lab 2E).

Em vez de guardar o ESTADO ATUAL, guardamos os EVENTOS: fatos imutáveis que aconteceram. O estado é o
resultado de aplicar os eventos em ordem. Um comando valida a regra de negócio contra o estado atual e,
se válido, devolve NOVOS eventos (nunca altera o passado).
"""
from dataclasses import dataclass, field
from datetime import datetime
from math import asin, cos, radians, sin, sqrt

RAIO_CONFIRMACAO_M = 100


class ErroDeDominio(Exception):
    pass


def distancia_m(lat1, lon1, lat2, lon2) -> float:
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    h = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(h))


# ---- eventos: (tipo, versão do esquema, dados). São dicionários simples, fáceis de gravar e de evoluir. -------------

def evento(tipo: str, dados: dict, ator: str, esquema: int = 1) -> dict:
    return {"tipo": tipo, "esquema": esquema, "dados": dados, "ator": ator}


def atualizar_esquema(e: dict) -> dict:
    """UPCASTING: eventos antigos são lidos no formato atual, sem reescrever o passado.

    EntregaReagendada v1 não tinha o motivo; a v2 tem. Um evento v1 é lido como v2 com motivo 'nao_informado'.
    """
    if e["tipo"] == "EntregaReagendada" and e["esquema"] == 1:
        return {**e, "esquema": 2, "dados": {**e["dados"], "motivo": "nao_informado"}}
    return e


@dataclass
class Entrega:
    id: str
    versao: int = 0
    status: str = "inexistente"
    codigo: str = ""
    transportadora: str = ""
    previsao: str = ""
    destino: tuple = (0.0, 0.0)
    reagendamentos: int = 0
    historico_de_status: list = field(default_factory=list)

    # ---- aplicar um evento ao estado (sem regras: o evento já aconteceu) ------------------------------------------
    def aplicar(self, e: dict) -> "Entrega":
        e = atualizar_esquema(e)
        d = e["dados"]
        if e["tipo"] == "EntregaRegistrada":
            self.status, self.codigo, self.transportadora = "criada", d["codigo"], d["transportadora"]
            self.previsao, self.destino = d["previsao"], (d["lat"], d["lon"])
        elif e["tipo"] == "RotaIniciada":
            self.status = "em_rota"
        elif e["tipo"] == "EntregaReagendada":
            self.previsao = d["nova_previsao"]
            self.reagendamentos += 1
        elif e["tipo"] == "EntregaConfirmada":
            self.status = "entregue"
        elif e["tipo"] == "EntregaCancelada":
            self.status = "cancelada"
        self.versao += 1
        return self

    @staticmethod
    def reconstruir(entrega_id: str, eventos: list[dict]) -> "Entrega":
        entrega = Entrega(entrega_id)
        for e in eventos:
            entrega.aplicar(e)
        return entrega

    # ---- comandos: validam a regra e devolvem NOVOS eventos ---------------------------------------------------------
    def registrar(self, codigo, transportadora, previsao, lat, lon, ator) -> list[dict]:
        if self.versao > 0:
            raise ErroDeDominio("entrega ja registrada")
        return [evento("EntregaRegistrada", {"codigo": codigo, "transportadora": transportadora,
                                             "previsao": previsao, "lat": lat, "lon": lon}, ator)]

    def iniciar_rota(self, motorista, ator) -> list[dict]:
        if self.status != "criada":
            raise ErroDeDominio(f"nao se inicia rota de entrega {self.status}")
        return [evento("RotaIniciada", {"motorista": motorista}, ator)]

    def reagendar(self, nova_previsao, motivo, ator) -> list[dict]:
        if self.status in ("inexistente", "entregue", "cancelada"):
            raise ErroDeDominio(f"nao se reagenda entrega {self.status}")
        return [evento("EntregaReagendada", {"nova_previsao": nova_previsao, "motivo": motivo}, ator, esquema=2)]

    def confirmar(self, lat, lon, ator) -> list[dict]:
        if self.status != "em_rota":
            raise ErroDeDominio(f"nao se confirma entrega {self.status}")
        d = distancia_m(lat, lon, *self.destino)
        if d > RAIO_CONFIRMACAO_M:
            raise ErroDeDominio(f"motorista a {d:.0f} m do destino (maximo {RAIO_CONFIRMACAO_M} m)")
        return [evento("EntregaConfirmada", {"lat": lat, "lon": lon, "distancia_m": round(d, 1)}, ator)]

    def cancelar(self, motivo, ator) -> list[dict]:
        if self.status in ("inexistente", "entregue", "cancelada"):
            raise ErroDeDominio(f"nao se cancela entrega {self.status}")
        return [evento("EntregaCancelada", {"motivo": motivo}, ator)]
