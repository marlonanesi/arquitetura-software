"""Adaptador EXTRA (terceiro provedor de mapas, simulado) para o exercício "adicione um adaptador".

Copie para src/confirmacao/adaptadores/ e registre na fábrica (veja o README do lab).
"""
from confirmacao.dominio.geo import Coordenada

# Terceiro formato de resposta: uma lista de objetos com lat/lon em texto
_RESPOSTAS = {
    "Rua das Flores, 100": [{"lat": "-23.5614", "lon": "-46.6559"}],
    "Av. Paulista, 1000": [{"lat": "-23.5632", "lon": "-46.6544"}],
}


class GeocodificadorOsm:
    def coordenada_de(self, endereco: str) -> Coordenada:
        resposta = _RESPOSTAS.get(endereco)
        if resposta is None:
            raise LookupError(f"endereco desconhecido para o provedor: {endereco}")
        return Coordenada(lat=float(resposta[0]["lat"]), lon=float(resposta[0]["lon"]))
