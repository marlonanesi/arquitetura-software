"""Adaptador do provedor "Google" (simulado, sem rede).

Cada provedor tem o seu formato de resposta. O adaptador traduz esse formato para a Coordenada do
domínio: o resto do sistema nunca vê a resposta do provedor.
"""
from confirmacao.dominio.geo import Coordenada

# O que a API do provedor devolveria (simulado)
_RESPOSTAS = {
    "Rua das Flores, 100": {"status": "OK", "results": [{"geometry": {"location": {"lat": -23.561400, "lng": -46.655900}}}]},
    "Av. Paulista, 1000": {"status": "OK", "results": [{"geometry": {"location": {"lat": -23.563200, "lng": -46.654400}}}]},
}


class GeocodificadorGoogle:
    def coordenada_de(self, endereco: str) -> Coordenada:
        resposta = _RESPOSTAS.get(endereco)
        if resposta is None:
            raise LookupError(f"endereco desconhecido para o provedor: {endereco}")
        local = resposta["results"][0]["geometry"]["location"]
        return Coordenada(lat=local["lat"], lon=local["lng"])
