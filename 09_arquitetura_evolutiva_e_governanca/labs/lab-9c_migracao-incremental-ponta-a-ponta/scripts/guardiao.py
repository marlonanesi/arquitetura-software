"""O GUARDIÃO: o critério de rollback, executado por máquina.

A cada 2 segundos, olha o que o gateway registrou nos últimos 10 segundos. Se a taxa de erros do serviço novo
passa de 5% (com pelo menos 20 leituras), liga o kill switch: TUDO volta ao legado, sem ninguém de plantão.
Ele só faz o ROLLBACK. A decisão de AVANÇAR (subir o percentual, virar a escrita) continua sendo de uma pessoa,
com os critérios de cada marco.
"""
import json
import time
from collections import deque

import httpx

import flags

GATEWAY = "http://gateway:8000"
JANELA_S, LIMITE_ERRO, MINIMO = 10, 0.05, 20
historico = deque()          # (instante, leituras_novo, erros_novo)

print(f"guardiao ativo: rollback automatico se erros do novo > {LIMITE_ERRO:.0%} em {JANELA_S} s (minimo {MINIMO} leituras)", flush=True)
while True:
    try:
        m = httpx.get(f"{GATEWAY}/metricas", timeout=3).json()
        agora = time.time()
        historico.append((agora, m["leituras_novo"] + m["erros_novo"], m["erros_novo"]))
        while historico and agora - historico[0][0] > JANELA_S:
            historico.popleft()
        tentativas = historico[-1][1] - historico[0][1]
        erros = historico[-1][2] - historico[0][2]
        ligado = flags.carregar()["flags"]["kill-switch-novo"]["defaultVariant"] == "ligado"
        if not ligado and tentativas >= MINIMO and erros / tentativas > LIMITE_ERRO:
            flags.definir_variante("kill-switch-novo", "ligado")
            print(f"{time.strftime('%H:%M:%S')} ROLLBACK AUTOMATICO: {erros} erros em {tentativas} leituras do novo "
                  f"({erros / tentativas:.0%}) nos ultimos {JANELA_S} s; kill switch LIGADO", flush=True)
            historico.clear()
    except Exception as erro:
        print(f"guardiao: {erro}", flush=True)
    time.sleep(2)
