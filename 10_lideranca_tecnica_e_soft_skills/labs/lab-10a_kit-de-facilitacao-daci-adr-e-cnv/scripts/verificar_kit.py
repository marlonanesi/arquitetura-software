"""Verifica os materiais do kit, para o aluno ver que "decisão bem comunicada" também se confere:

  1. DACI: um único Driver e um único Approver, ao menos um Contributor e um Informed, e uma data de decisão
  2. ADR do exemplo: formato válido (mesmas regras dos labs 1A e 9B)
  3. Uma decisão, três públicos: os mesmos fatos em todos os documentos, o vocabulário certo e o tamanho certo

  python scripts/verificar_kit.py            roda tudo sobre o exemplo bom
  python scripts/verificar_kit.py --ruins    roda sobre os exemplos ruins (deve falhar de propósito)
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parent.parent
ruins = "--ruins" in sys.argv
problemas: list[str] = []


def palavras(texto: str) -> int:
    return len(re.findall(r"\w+", texto))


# ---- 1. DACI ---------------------------------------------------------------------------------------------
def verificar_daci(caminho: Path) -> list[str]:
    texto = caminho.read_text(encoding="utf-8")
    erros = []
    papeis = re.findall(r"^\|\s*([DACI]) \((?:Driver|Approver|Contributor|Informed)\)\s*\|", texto, re.M)
    contagem = {p: papeis.count(p) for p in "DACI"}
    if contagem["D"] != 1:
        erros.append(f"deve haver exatamente 1 Driver (D), ha {contagem['D']}")
    if contagem["A"] != 1:
        erros.append(f"deve haver exatamente 1 Approver (A), ha {contagem['A']}")
    if contagem["C"] < 1:
        erros.append("deve haver ao menos 1 Contributor (C)")
    if contagem["I"] < 1:
        erros.append("deve haver ao menos 1 Informed (I)")
    if not re.search(r"\*\*Decisão até:\*\*\s*\d{4}-\d{2}-\d{2}", texto):
        erros.append("falta 'Decisão até:' com uma data AAAA-MM-DD")
    if len(re.findall(r"^\| [A-Z]\w* \|.*\|.*\|.*\|$", texto, re.M)) < 2 and "| Opção |" in texto:
        erros.append("a decisão precisa de pelo menos 2 opções")
    return erros


alvo_daci = RAIZ / "01_daci" / ("exemplo-daci-ruim.md" if ruins else "exemplo-service-mesh.md")
erros = verificar_daci(alvo_daci)
print(f"[DACI] {alvo_daci.name}: " + ("ok (1 Driver, 1 Approver, contribuintes, informados e prazo)" if not erros else f"{len(erros)} problema(s)"))
for e in erros:
    print(f"   - {e}")
problemas += erros

# ---- 2. ADR ---------------------------------------------------------------------------------------------
if not ruins:
    texto = (RAIZ / "02_sessao_de_decisao" / "adr-resultado-exemplo.md").read_text(encoding="utf-8")
    erros = []
    if not re.match(r"---\nstatus: (proposed|accepted|rejected|deprecated|superseded by ADR-\d{4})\ndate: \d{4}-\d{2}-\d{2}\ndecision-makers: .+\n---\n# \d{4}\. ", texto):
        erros.append("cabecalho invalido (status, date, decision-makers e titulo '# NNNN. ...')")
    for secao in ("Contexto e problema", "Decisão", "Consequências"):
        if f"## {secao}" not in texto:
            erros.append(f"falta a secao '## {secao}'")
    print("[ADR] adr-resultado-exemplo.md: " + ("ok" if not erros else f"{len(erros)} problema(s)"))
    for e in erros:
        print(f"   - {e}")
    problemas += erros

# ---- 3. uma decisão, três públicos ----------------------------------------------------------------------
pasta = RAIZ / "04_uma_decisao_tres_publicos"
config = json.loads((pasta / "fatos.json").read_text(encoding="utf-8"))
exemplos = {"para-tech-lead.md": pasta / "para-tech-lead.md", "para-cfo.md": pasta / "para-cfo.md", "para-board.md": pasta / "para-board.md"}
if ruins:
    exemplos = {k: RAIZ / "04_uma_decisao_tres_publicos" / "ruins" / k for k in exemplos}
for nome, caminho in exemplos.items():
    texto = caminho.read_text(encoding="utf-8")
    regras = config["por_publico"][nome]
    erros = []
    for fato in config["fatos_obrigatorios_em_todos"]:
        if fato not in texto:
            erros.append(f"falta o fato '{fato}' (os numeros precisam ser iguais em todos os publicos)")
    for termo in regras["termos_obrigatorios"]:
        if termo.lower() not in texto.lower():
            erros.append(f"falta o termo '{termo}', que este publico precisa ouvir")
    for jargao in regras.get("jargao_proibido", []):
        if re.search(rf"\b{re.escape(jargao)}\b", texto, re.I):
            erros.append(f"jargao '{jargao}' que este publico nao precisa ver")
    n = palavras(texto)
    if n > regras["max_palavras"]:
        erros.append(f"{n} palavras: passa do limite de {regras['max_palavras']} para este publico")
    print(f"[PUBLICO] {nome} ({n} palavras): " + ("ok" if not erros else f"{len(erros)} problema(s)"))
    for e in erros:
        print(f"   - {e}")
    problemas += erros

print()
if problemas:
    print(f"RESULTADO: {len(problemas)} problema(s)")
    sys.exit(1)
print("RESULTADO: o kit esta consistente")
