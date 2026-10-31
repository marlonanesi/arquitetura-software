"""Diagnóstico de débito técnico por hotspots: cruza a frequência de mudança (Git) com a complexidade (lizard).

  python hotspots.py REPOSITORIO [--desde "12 months ago"] [--ext py,js,ts,java,go,cs] [--top 10]
                                 [--ignorar tests/,docs/] [--saida /saida]

A ideia (a de Adam Tornhill): o código que MUDA MUITO e é COMPLEXO é onde o débito mais custa. Código
complexo que ninguém toca é só um risco adormecido; código que muda muito mas é simples costuma ser
configuração. Só pelo histórico do repositório, sem ferramenta paga.

Produz, em --saida: hotspots.md, hotspots.csv e relatorio.html (com um gráfico de dispersão).
"""
import argparse
import csv
import html
import itertools
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import lizard

p = argparse.ArgumentParser()
p.add_argument("repo")
p.add_argument("--desde", default="12 months ago")
p.add_argument("--ext", default="py,js,ts,tsx,java,go,cs,rb,php,kt")
p.add_argument("--top", type=int, default=10)
p.add_argument("--ignorar", default="")
p.add_argument("--saida", default="/saida")
p.add_argument("--limite", type=float, default=0.4, help="fração do máximo a partir da qual mudança e complexidade são 'altas' (padrão 0.4)")
a = p.parse_args()

REPO = Path(a.repo)
EXTENSOES = {"." + e.strip(".") for e in a.ext.split(",")}
IGNORAR = [x for x in a.ignorar.split(",") if x]


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def relevante(caminho: str) -> bool:
    return Path(caminho).suffix in EXTENSOES and not any(caminho.startswith(i) for i in IGNORAR)


# ---- 1. histórico: commits, linhas, autores, arquivos por commit -----------------------------------
saida_git = git("log", f"--since={a.desde}", "--numstat", "--format=@@%H|%an", "--no-renames")
commits = []                 # lista de (autor, [arquivos])
churn = Counter()            # commits que tocaram o arquivo
linhas = Counter()           # linhas adicionadas + removidas
autores = defaultdict(Counter)
atual = None
for linha in saida_git.splitlines():
    if linha.startswith("@@"):
        _, autor = linha[2:].split("|", 1)
        atual = (autor, [])
        commits.append(atual)
    elif linha.strip() and atual is not None:
        add, rem, caminho = linha.split("\t", 2)
        if add == "-" or not relevante(caminho):
            continue
        atual[1].append(caminho)
        churn[caminho] += 1
        linhas[caminho] += int(add) + int(rem)
        autores[caminho][atual[0]] += 1

if not commits:
    sys.exit(f"nenhum commit em {REPO} desde '{a.desde}'")

# ---- 2. complexidade do código ATUAL -------------------------------------------------------------
arquivos = []
for caminho, n in churn.items():
    f = REPO / caminho
    if not f.exists():                       # o arquivo foi removido desde então
        continue
    info = lizard.analyze_file(str(f))
    ccn = sum(fn.cyclomatic_complexity for fn in info.function_list)
    maior = max((fn.cyclomatic_complexity for fn in info.function_list), default=0)
    dono, commits_do_dono = autores[caminho].most_common(1)[0]
    arquivos.append({"arquivo": caminho, "mudancas": n, "linhas": linhas[caminho], "ccn": ccn, "maior_funcao": maior,
                     "nloc": info.nloc, "autores": len(autores[caminho]), "dono": dono, "parte_do_dono": commits_do_dono / n})

max_mud = max(x["mudancas"] for x in arquivos)
max_ccn = max(x["ccn"] for x in arquivos) or 1
limite_mud = a.limite * max_mud          # a partir daqui, o arquivo "muda muito"
limite_ccn = a.limite * max_ccn          # a partir daqui, o arquivo "é complexo"
for x in arquivos:
    x["pontuacao"] = (x["mudancas"] / max_mud) * (x["ccn"] / max_ccn)
    alto_mud, alto_ccn = x["mudancas"] >= limite_mud, x["ccn"] >= limite_ccn
    x["quadrante"] = ("hotspot" if alto_mud and alto_ccn else
                      "complexo e quieto" if alto_ccn else "agitado e simples" if alto_mud else "saudavel")
arquivos.sort(key=lambda x: x["pontuacao"], reverse=True)

# ---- 3. acoplamento temporal: arquivos que mudam juntos ---------------------------------------------
pares = Counter()
for _, arqs in commits:
    unicos = sorted(set(arqs))
    if 2 <= len(unicos) <= 15:               # commits enormes (refatorações em massa) distorcem a análise
        for x, y in itertools.combinations(unicos, 2):
            pares[(x, y)] += 1


def depende(x: str, y: str) -> bool:
    """Heurística simples: o nome do módulo de um aparece no código do outro (import)."""
    for origem, destino in ((x, y), (y, x)):
        try:
            if re.search(rf"\b{re.escape(Path(destino).stem)}\b", (REPO / origem).read_text(encoding="utf-8", errors="ignore")):
                return True
        except OSError:
            pass
    return False


acoplamentos = []
for (x, y), co in pares.items():
    if co < 5 or not (REPO / x).exists() or not (REPO / y).exists():
        continue
    grau = co / min(churn[x], churn[y])
    if grau >= 0.5:
        acoplamentos.append({"a": x, "b": y, "juntos": co, "grau": grau, "dependencia_estatica": depende(x, y)})
acoplamentos.sort(key=lambda c: (c["grau"], c["juntos"]), reverse=True)

# ---- 4. saídas -------------------------------------------------------------------------------------
destino = Path(a.saida)
destino.mkdir(parents=True, exist_ok=True)
topo = arquivos[: a.top]

with open(destino / "hotspots.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(arquivos[0]))
    w.writeheader()
    w.writerows(arquivos)

md = [f"# Hotspots de {REPO.name}", "",
      f"Periodo: desde '{a.desde}'. {len(commits)} commits, {len(arquivos)} arquivos de codigo analisados.", "",
      "## Os maiores hotspots (mudanca x complexidade)", "",
      "| # | Arquivo | Mudancas | Complexidade | Quadrante | Autores | Dono (parte dos commits) |", "|---|---|---|---|---|---|---|"]
for i, x in enumerate(topo, 1):
    md.append(f"| {i} | `{x['arquivo']}` | {x['mudancas']} | {x['ccn']} | {x['quadrante']} | {x['autores']} | {x['dono']} ({x['parte_do_dono']:.0%}) |")
md += ["", "## Acoplamento temporal (arquivos que mudam juntos)", "",
       "| Arquivo A | Arquivo B | Juntos | Grau | Dependencia no codigo |", "|---|---|---|---|---|"]
for c in acoplamentos[:10]:
    md.append(f"| `{c['a']}` | `{c['b']}` | {c['juntos']} | {c['grau']:.0%} | {'sim' if c['dependencia_estatica'] else '**nao (oculto)**'} |")
(destino / "hotspots.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def svg() -> str:
    L, T, W, H = 70, 20, 640, 360
    px = lambda m: L + (m / max_mud) * (W - 20)
    py = lambda c: T + H - (c / max_ccn) * (H - 20)
    cores = {"hotspot": "#c0392b", "complexo e quieto": "#d68910", "agitado e simples": "#2e86c1", "saudavel": "#7f8c8d"}
    partes = [f'<svg viewBox="0 0 {L + W} {T + H + 50}" width="100%" role="img" aria-label="Dispersao de mudancas por complexidade">',
              f'<line x1="{px(limite_mud)}" y1="{T}" x2="{px(limite_mud)}" y2="{T + H}" stroke="#bbb" stroke-dasharray="4"/>',
              f'<line x1="{L}" y1="{py(limite_ccn)}" x2="{L + W - 20}" y2="{py(limite_ccn)}" stroke="#bbb" stroke-dasharray="4"/>',
              f'<line x1="{L}" y1="{T + H}" x2="{L + W - 20}" y2="{T + H}" stroke="#333"/>',
              f'<line x1="{L}" y1="{T}" x2="{L}" y2="{T + H}" stroke="#333"/>',
              f'<text x="{L + (W - 20) / 2}" y="{T + H + 36}" text-anchor="middle" font-size="13">mudancas no periodo (churn)</text>',
              f'<text transform="translate(18,{T + H / 2}) rotate(-90)" text-anchor="middle" font-size="13">complexidade ciclomatica</text>',
              f'<text x="{px(limite_mud) + 8}" y="{T + 14}" font-size="12" fill="#c0392b">HOTSPOTS (muda muito e e complexo)</text>']
    for i, x in enumerate(arquivos):
        cx, cy = px(x["mudancas"]), py(x["ccn"])
        partes.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{5 + 14 * x["pontuacao"]:.1f}" fill="{cores[x["quadrante"]]}" fill-opacity="0.65"><title>{html.escape(x["arquivo"])}: {x["mudancas"]} mudancas, complexidade {x["ccn"]}</title></circle>')
        if i < 5 or x["quadrante"] != "saudavel":
            perto_da_borda = cx > L + 0.7 * W
            ancora, dx = ("end", -(10 + 14 * x["pontuacao"])) if perto_da_borda else ("start", 8)
            partes.append(f'<text x="{cx + dx:.1f}" y="{cy - 8 - (i % 2) * 13:.1f}" text-anchor="{ancora}" font-size="11">{html.escape(Path(x["arquivo"]).name)}</text>')
    partes.append("</svg>")
    return "\n".join(partes)


def tabela(cabecalhos, linhas_):
    cab = "".join(f"<th>{c}</th>" for c in cabecalhos)
    corpo = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>" for l in linhas_)
    return f"<table><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table>"


pagina = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Hotspots de {html.escape(REPO.name)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#222}}
table{{border-collapse:collapse;width:100%;margin:1rem 0}}th,td{{border-bottom:1px solid #ddd;padding:.4rem .5rem;text-align:left;font-size:.9rem}}
th{{background:#f4f4f4}}.leg span{{display:inline-block;margin-right:1rem}}.leg i{{display:inline-block;width:.8rem;height:.8rem;border-radius:50%;margin-right:.3rem}}</style>
<h1>Hotspots de {html.escape(REPO.name)}</h1>
<p>{len(commits)} commits desde "{html.escape(a.desde)}", {len(arquivos)} arquivos de codigo. Cada bolha e um arquivo: quanto mais para a direita, mais ele muda; quanto mais alto, mais complexo; quanto maior a bolha, maior a pontuacao (mudanca x complexidade).</p>
<div class="leg"><span><i style="background:#c0392b"></i>hotspot</span><span><i style="background:#d68910"></i>complexo e quieto</span><span><i style="background:#2e86c1"></i>agitado e simples</span><span><i style="background:#7f8c8d"></i>saudavel</span></div>
{svg()}
<h2>Os maiores hotspots</h2>
{tabela(["#", "Arquivo", "Mudancas", "Complexidade", "Quadrante", "Autores", "Dono"],
        [[i, f"<code>{html.escape(x['arquivo'])}</code>", x["mudancas"], x["ccn"], x["quadrante"], x["autores"], f"{html.escape(x['dono'])} ({x['parte_do_dono']:.0%})"] for i, x in enumerate(topo, 1)])}
<h2>Acoplamento temporal</h2><p>Arquivos que mudam juntos com frequencia. Sem dependencia no codigo, e um acoplamento oculto.</p>
{tabela(["Arquivo A", "Arquivo B", "Juntos", "Grau", "Dependencia no codigo"],
        [[f"<code>{html.escape(c['a'])}</code>", f"<code>{html.escape(c['b'])}</code>", c["juntos"], f"{c['grau']:.0%}", "sim" if c["dependencia_estatica"] else "<b>nao (oculto)</b>"] for c in acoplamentos[:10]])}
</html>"""
(destino / "relatorio.html").write_text(pagina, encoding="utf-8")

# ---- 5. resumo no terminal ---------------------------------------------------------------------------
print(f"{len(commits)} commits, {len(arquivos)} arquivos analisados (limites: {limite_mud:.0f} mudancas e complexidade {limite_ccn:.0f}, ou seja, {a.limite:.0%} do maximo)\n")
print(f"{'#':>2} {'arquivo':<26}{'mudancas':>9}{'complex.':>9}  {'quadrante':<18}{'autores':>8}  dono")
for i, x in enumerate(topo, 1):
    print(f"{i:>2} {x['arquivo']:<26}{x['mudancas']:>9}{x['ccn']:>9}  {x['quadrante']:<18}{x['autores']:>8}  {x['dono']} ({x['parte_do_dono']:.0%})")
print("\nAcoplamento temporal:")
for c in acoplamentos[:5]:
    print(f"  {c['a']} <-> {c['b']}: juntos em {c['juntos']} commits ({c['grau']:.0%}); dependencia no codigo: {'sim' if c['dependencia_estatica'] else 'NAO (oculto)'}")
print(f"\nrelatorios em {destino}: relatorio.html, hotspots.md, hotspots.csv")
