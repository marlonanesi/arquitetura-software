"""Valida o arquivo CODEOWNERS: nenhuma área do repositório sem dono, e áreas críticas com dois responsáveis.

  python verificar_codeowners.py [CODEOWNERS]

Regras:
  1. toda pasta e todo arquivo de primeiro nível do repositório precisa ser coberto por uma linha do CODEOWNERS
  2. as áreas críticas (decisões, políticas, exceções e o próprio CODEOWNERS) exigem pelo menos 2 responsáveis
  3. todo responsável tem o formato @pessoa ou @organizacao/time
"""
import fnmatch
import re
import sys
from pathlib import Path

ARQUIVO = Path(sys.argv[1] if len(sys.argv) > 1 else "CODEOWNERS")
CRITICAS = ["/adrs/", "/politicas/", "/excecoes/", "/CODEOWNERS"]
IGNORAR = {".git", ".github", "__pycache__", ".gitignore", "INDICE_ADRS.md", "README.md"}

regras = []
problemas = []
for numero, linha in enumerate(ARQUIVO.read_text(encoding="utf-8").splitlines(), 1):
    linha = linha.strip()
    if not linha or linha.startswith("#"):
        continue
    padrao, *donos = linha.split()
    for dono in donos:
        if not re.fullmatch(r"@[\w.-]+(/[\w.-]+)?", dono):
            problemas.append(f"linha {numero}: responsavel invalido '{dono}'")
    regras.append((padrao, donos))


def cobre(padrao: str, caminho: str) -> bool:
    if padrao.endswith("/"):
        return caminho.startswith(padrao.lstrip("/"))
    if padrao.startswith("/"):
        return fnmatch.fnmatch(caminho, padrao.lstrip("/"))
    return fnmatch.fnmatch(Path(caminho).name, padrao)


def donos_de(caminho: str):
    achados = [donos for padrao, donos in regras if cobre(padrao, caminho)]
    return achados[-1] if achados else None      # a última regra que casa vence, como no GitHub


for item in sorted(Path(".").iterdir()):
    if item.name in IGNORAR or item.name.startswith("."):
        continue
    caminho = item.name + ("/" if item.is_dir() else "")
    if donos_de(caminho) is None:
        problemas.append(f"'{caminho}' nao tem dono no CODEOWNERS")

for critica in CRITICAS:
    donos = next((d for p, d in regras if p == critica), None)
    if donos is None:
        problemas.append(f"a area critica '{critica}' nao esta no CODEOWNERS")
    elif len(donos) < 2:
        problemas.append(f"a area critica '{critica}' precisa de pelo menos 2 responsaveis (tem {len(donos)})")

if problemas:
    print(f"{len(problemas)} problema(s) no CODEOWNERS:")
    for p in problemas:
        print(f"  - {p}")
    sys.exit(1)
print(f"CODEOWNERS valido: {len(regras)} regras, areas criticas com dois responsaveis")
