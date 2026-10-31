"""A virada de janela: o ponto fraco da janela fixa.

Envia LIMITE requisições logo ANTES do fim de uma janela e LIMITE logo DEPOIS do início da seguinte,
por algoritmo, e conta quantas foram aceitas. O limite é de LIMITE por JANELA_S segundos.
"""
import json
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

BASE = os.environ.get("BASE", "http://localhost:8501")


def chamar(caminho: str, chave: str) -> int:
    pedido = urllib.request.Request(f"{BASE}{caminho}", headers={"X-Api-Key": chave})
    try:
        with urllib.request.urlopen(pedido, timeout=5) as resposta:
            return resposta.status
    except urllib.error.HTTPError as erro:
        return erro.code


def disparar(caminho: str, chave: str, n: int) -> int:
    with ThreadPoolExecutor(max_workers=n) as pool:
        codigos = list(pool.map(lambda _: chamar(caminho, chave), range(n)))
    return codigos.count(200)


config = json.load(urllib.request.urlopen(f"{BASE}/config"))
limite, janela = config["limite"], config["janela_s"]
print(f"limite: {limite} requisicoes por janela de {janela:g} s\n")

resultados = {}
for algoritmo in ("fixa", "deslizante", "bucket"):
    chave = f"virada-{algoritmo}-{int(time.time())}"
    # sincroniza com o relógio: 0,25 s antes do fim da próxima janela
    agora = time.time()
    proximo_fim = (int(agora // janela) + 1) * janela
    if proximo_fim - agora < 1.0:
        proximo_fim += janela
    time.sleep(proximo_fim - 0.25 - time.time())
    antes = disparar(f"/{algoritmo}", chave, limite)
    time.sleep(max(0, proximo_fim + 0.05 - time.time()))
    depois = disparar(f"/{algoritmo}", chave, limite)
    resultados[algoritmo] = (antes, depois)

print(f"{'algoritmo':<12} {'antes da virada':>16} {'depois da virada':>17} {'em ~0,3 s':>11}")
for algoritmo, (antes, depois) in resultados.items():
    print(f"{algoritmo:<12} {antes:>16} {depois:>17} {antes + depois:>11}")
print(f"\n(o limite declarado e {limite} por {janela:g} s)")
