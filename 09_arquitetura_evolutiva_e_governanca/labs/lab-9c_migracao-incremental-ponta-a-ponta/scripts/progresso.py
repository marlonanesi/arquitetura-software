"""O PAINEL DE PROGRESSO da migração: cada marco, o seu critério de saída e se ele está atendido agora.

  python progresso.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import psycopg

import flags

sys.stdout.reconfigure(encoding="utf-8")
m = httpx.get("http://gateway:8000/metricas", timeout=5).json()
f = flags.estado()
leituras = m["leituras_novo"] + m["leituras_legado"]
pct_novo = (m["leituras_novo"] / leituras * 100) if leituras else 0
tentativas_novo = m["leituras_novo"] + m["erros_novo"]
taxa_erro_novo = (m["erros_novo"] / tentativas_novo) if tentativas_novo else 0
sombra_total = m["sombra_iguais"] + m["sombra_divergentes"]

with psycopg.connect("postgresql://luna:luna@postgres:5432/legado") as cl, psycopg.connect("postgresql://luna:luna@postgres:5432/novo") as cn:
    n_legado = cl.execute("SELECT count(*) FROM entrega_tb").fetchone()[0]
    n_novo = cn.execute("SELECT count(*) FROM entregas").fetchone()[0]
    fila = cl.execute("SELECT count(*) FROM fila_reparo").fetchone()[0]
resultado = subprocess.run([sys.executable, "dados.py", "verificar"], capture_output=True, text=True)
consistente = resultado.returncode == 0

marcos = [
    ("M1", "Historico copiado (backfill)", "banco novo com as mesmas entregas do legado", n_novo >= n_legado, f"{n_novo}/{n_legado}"),
    ("M2", "Dual-write consistente", "escrita = dupla (ou novo), bancos consistentes, fila de reparo vazia", f["escrita"] in ("dupla", "novo") and consistente and fila == 0,
     f"escrita={f['escrita']}, {'consistentes' if consistente else 'DIVERGENTES'}, fila de reparo={fila}"),
    ("M3", "Modo sombra sem divergencia", ">= 100 comparacoes e 0 divergencias", sombra_total >= 100 and m["sombra_divergentes"] == 0,
     f"{m['sombra_iguais']} iguais, {m['sombra_divergentes']} divergentes"),
    ("M4", "Canario de leitura saudavel", "leitura do novo > 0% e erros do novo < 1%", f["leitura_novo_pct"] > 0 and tentativas_novo >= 20 and taxa_erro_novo < 0.01,
     f"{f['leitura_novo_pct']}% liberado, erros {taxa_erro_novo:.1%} em {tentativas_novo} leituras"),
    ("M5", "Leitura 100% e escrita no novo", "leitura 100%, escrita = novo, kill switch desligado", f["leitura_novo_pct"] == 100 and f["escrita"] == "novo" and f["kill_switch_novo"] == "desligado",
     f"leitura {f['leitura_novo_pct']}%, escrita={f['escrita']}, kill switch={f['kill_switch_novo']}"),
    ("M6", "Legado sem trafego, pronto para desligar", "leitura 100% no novo e nenhuma leitura chegando ao legado (>= 100 leituras na janela)", leituras >= 100 and m["leituras_legado"] == 0 and f["leitura_novo_pct"] == 100,
     f"{pct_novo:.1f}% das leituras no novo, {m['leituras_legado']} no legado"),
]

print(f"Flags: leitura do novo = {f['leitura_novo_pct']}% | sombra = {f['sombra']} | escrita = {f['escrita']} | kill switch = {f['kill_switch_novo']}")
print(f"Leituras acumuladas: novo = {m['leituras_novo']}, legado = {m['leituras_legado']} ({pct_novo:.0f}% pelo novo) | fallbacks = {m['fallbacks']} | latencia media (ms): {m['latencia_media_ms']}\n")
# Os marcos atingidos ficam registrados (as métricas são por janela e zeram entre os marcos)
registro = Path("/flags/marcos.json")
atingidos = json.loads(registro.read_text(encoding="utf-8")) if registro.exists() else {}
for sigla, _, _, ok, _ in marcos:
    if ok and sigla not in atingidos:
        atingidos[sigla] = time.strftime("%H:%M:%S")
registro.write_text(json.dumps(atingidos), encoding="utf-8")

print(f"{'':<4}{'marco':<42}{'situacao':<22}{'agora'}")
for sigla, nome, criterio, ok, agora in marcos:
    situacao = "ATENDIDO" if ok else (f"atendido as {atingidos[sigla]}" if sigla in atingidos else "pendente")
    print(f"{sigla:<4}{nome:<42}{situacao:<22}{agora}")
    print(f"    criterio: {criterio}")
