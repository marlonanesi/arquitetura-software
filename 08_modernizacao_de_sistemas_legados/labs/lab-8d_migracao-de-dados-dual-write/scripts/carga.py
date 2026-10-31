"""Tráfego de escrita contínuo no serviço, para simular o sistema EM PRODUÇÃO durante a migração.

  python carga.py [segundos] [por_segundo]     (padrão: 20 s, 40 escritas por segundo)

80% das escritas alteram entregas existentes; 20% criam entregas novas. O legado não para durante a migração.
"""
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE = "http://api:8000"
segundos = int(sys.argv[1]) if len(sys.argv) > 1 else 20
taxa = int(sys.argv[2]) if len(sys.argv) > 2 else 40
tz = ["transrapida", "veloz", "boreal"]
status = ["aguardando_coleta", "em_rota", "entregue", "cancelada"]
contador = {"ok": 0, "erro": 0, "novas": 0}
trava = threading.Lock()
proximo_id = [random.randint(100000, 900000)]   # ids novos que nao colidem entre execucoes


def uma_escrita(_):
    if random.random() < 0.2:
        with trava:
            n = proximo_id[0]
            proximo_id[0] += 1
            contador["novas"] += 1
    else:
        n = random.choice([i for i in random.sample(range(1, 20001), 20) if i % 97 and i % 89])
    corpo = {"id": f"E-{n:06d}", "status": random.choice(status), "previsao": "2026-12-15",
             "valor_centavos": random.randint(1000, 500000), "transportadora_id": random.choice(tz)}
    try:
        r = httpx.post(f"{BASE}/entregas", json=corpo, timeout=5)
        with trava:
            contador["ok" if r.status_code == 201 else "erro"] += 1
    except httpx.HTTPError:
        with trava:
            contador["erro"] += 1


inicio = time.time()
with ThreadPoolExecutor(max_workers=16) as pool:
    for _ in range(segundos * taxa):
        pool.submit(uma_escrita, None)
        time.sleep(1 / taxa)
print(f"carga concluida em {time.time() - inicio:.0f} s: {contador['ok']} escritas ok ({contador['novas']} entregas novas), {contador['erro']} erros")
