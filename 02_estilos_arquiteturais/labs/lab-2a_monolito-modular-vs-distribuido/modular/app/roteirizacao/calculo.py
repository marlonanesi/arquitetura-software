"""Cálculo da sequência de paradas (simulado: custa uns 20 ms)."""
import time


def calcular(destino: str) -> dict:
    time.sleep(0.02)
    motoristas = ["Ana", "Bruno", "Carla", "Diego"]
    indice = sum(map(ord, destino)) % len(motoristas)
    return {"sequencia": indice + 1, "motorista": motoristas[indice]}
