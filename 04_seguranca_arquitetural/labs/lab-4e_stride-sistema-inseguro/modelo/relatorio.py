"""Lê o JSON do pytm e escreve um resumo das ameaças: por severidade e por elemento do diagrama."""
import json
import sys
from collections import Counter

caminho, saida, variante = sys.argv[1], sys.argv[2], sys.argv[3]
dados = json.load(open(caminho, encoding="utf-8"))
achados = dados["findings"]
por_sev = Counter(a["severity"] for a in achados)
por_alvo = Counter(a["target"] for a in achados)
ordem = {"Very High": 0, "High": 1, "Medium": 2, "Low": 3, "Very low": 4}

linhas = [f"# Ameacas deduzidas pelo pytm: {variante}", "",
          f"Total: **{len(achados)}** ameacas em {len(por_alvo)} elementos do diagrama.", "",
          "| Severidade | Quantidade |", "|---|---|"]
for sev in sorted(por_sev, key=lambda s: ordem.get(s, 9)):
    linhas.append(f"| {sev} | {por_sev[sev]} |")
linhas += ["", "## Por elemento", "", "| Elemento | Ameacas |", "|---|---|"]
for alvo, n in por_alvo.most_common():
    linhas.append(f"| {alvo} | {n} |")
linhas += ["", "## Ameacas mais severas", "", "| Id | Elemento | Ameaca | Severidade |", "|---|---|---|---|"]
for a in sorted(achados, key=lambda a: (ordem.get(a["severity"], 9), a["threat_id"]))[:15]:
    linhas.append(f"| {a['threat_id']} | {a['target']} | {a['description']} | {a['severity']} |")
open(saida, "w", encoding="utf-8").write("\n".join(linhas) + "\n")
print(f"{variante}: {len(achados)} ameacas  " + "  ".join(f"{s}={por_sev[s]}" for s in sorted(por_sev, key=lambda s: ordem.get(s, 9))))
