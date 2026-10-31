"""Tráfego de usuários reais passando pelo gateway: 90% leituras e 10% escritas, de 200 usuários diferentes.

  python carga.py [segundos] [por_segundo]     (padrão: 30 s, 40 requisições por segundo)
"""
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

GATEWAY = "http://gateway:8000"
segundos = int(sys.argv[1]) if len(sys.argv) > 1 else 30
taxa = int(sys.argv[2]) if len(sys.argv) > 2 else 40
cont = {"ok": 0, "erro": 0, "novo": 0, "legado": 0}
trava = threading.Lock()
cliente = httpx.Client(timeout=8)


def uma():
    usuario = f"u{random.randint(1, 200)}"
    try:
        if random.random() < 0.9:
            r = cliente.get(f"{GATEWAY}/entregas/E-{random.randint(1, 2000):06d}", headers={"X-Usuario": usuario})
            ok = r.status_code == 200
            fonte = r.json().get("fonte") if ok else None
        else:
            n = random.randint(1, 2000)
            r = cliente.post(f"{GATEWAY}/entregas", headers={"X-Usuario": usuario},
                             json={"id": f"E-{n:06d}", "status": random.choice(["em_rota", "entregue"]), "previsao": "2026-12-15",
                                   "valor_centavos": random.randint(1000, 500000), "transportadora_id": random.choice(["veloz", "boreal", "transrapida"])})
            ok, fonte = r.status_code == 201, None
        with trava:
            cont["ok" if ok else "erro"] += 1
            if fonte:
                cont[fonte] += 1
    except httpx.HTTPError:
        with trava:
            cont["erro"] += 1


inicio = time.time()
with ThreadPoolExecutor(max_workers=24) as pool:
    for _ in range(segundos * taxa):
        pool.submit(uma)
        time.sleep(1 / taxa)
total = cont["ok"] + cont["erro"]
print(f"carga: {total} requisicoes em {time.time() - inicio:.0f} s | ok={cont['ok']} erros_para_o_cliente={cont['erro']} | leituras: novo={cont['novo']} legado={cont['legado']}")
