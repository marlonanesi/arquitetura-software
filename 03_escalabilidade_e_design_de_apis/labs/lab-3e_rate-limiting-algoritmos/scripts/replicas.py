"""Limite compartilhado entre réplicas: contador na memória de cada réplica x contador no Redis.

Com duas réplicas atrás de um balanceador round-robin, envia 2 x LIMITE requisições dentro de uma
mesma janela e conta quantas são aceitas. O limite declarado é de LIMITE por janela.
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = os.environ.get("BASE", "http://localhost:8501")


def chamar(armazenamento: str, chave: str):
    pedido = urllib.request.Request(f"{BASE}/fixa?armazenamento={armazenamento}", headers={"X-Api-Key": chave})
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            return resposta.status, resposta.headers.get("X-Replica")
    except urllib.error.HTTPError as erro:
        return erro.code, erro.headers.get("X-Replica")


config = json.load(urllib.request.urlopen(f"{BASE}/config"))
limite, janela = config["limite"], config["janela_s"]
print(f"limite: {limite} requisicoes por janela de {janela:g} s; enviando {2 * limite} em sequencia\n")

for armazenamento in ("memoria", "redis"):
    chave = f"replicas-{armazenamento}-{int(time.time())}"
    agora = time.time()
    inicio_proxima = (int(agora // janela) + 1) * janela
    time.sleep(inicio_proxima + 0.1 - agora)        # começa logo no início de uma janela
    aceitas = {"api1": 0, "api2": 0}
    recusadas = 0
    for _ in range(2 * limite):
        codigo, replica = chamar(armazenamento, chave)
        if codigo == 200:
            aceitas[replica] = aceitas.get(replica, 0) + 1
        else:
            recusadas += 1
    total = sum(aceitas.values())
    print(f"{armazenamento:<8} aceitas={total:>2} (api1={aceitas.get('api1', 0)}, api2={aceitas.get('api2', 0)})  recusadas={recusadas}")
print(f"\n(com o contador correto, o total aceito seria {limite})")
