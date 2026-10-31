"""Adaptador do provedor "HERE" (simulado, sem rede): outro formato de resposta, o mesmo contrato."""
from confirmacao.dominio.geo import Coordenada

# O que a API do provedor devolveria (simulado). Repare: outra estrutura, outros nomes de campo.
_RESPOSTAS = {
    "Rua das Flores, 100": {"items": [{"position": {"lat": -23.561420, "lng": -46.655880}}]},
    "Av. Paulista, 1000": {"items": [{"position": {"lat": -23.563210, "lng": -46.654390}}]},
}


class GeocodificadorHere:
    def coordenada_de(self, endereco: str) -> Coordenada:
        resposta = _RESPOSTAS.get(endereco)
        if resposta is None:
            raise LookupError(f"endereco desconhecido para o provedor: {endereco}")
        posicao = resposta["items"][0]["position"]
        return Coordenada(lat=posicao["lat"], lon=posicao["lng"])
