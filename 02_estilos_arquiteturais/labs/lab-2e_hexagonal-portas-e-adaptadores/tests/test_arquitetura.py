"""Teste de ARQUITETURA: a regra de dependência, verificada por máquina.

Regra: o pacote "dominio" só pode importar a biblioteca padrão pura e ele mesmo. Nada de adaptadores,
de drivers de banco, de clientes HTTP ou de frameworks.
"""
import ast
from pathlib import Path

DOMINIO = Path(__file__).resolve().parent.parent / "src" / "confirmacao" / "dominio"

# Biblioteca padrão "pura" permitida no domínio (sem I/O)
PERMITIDOS = {"dataclasses", "datetime", "enum", "math", "typing", "abc", "decimal", "__future__"}
INTERNOS = "confirmacao.dominio"


def importacoes(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            nomes.add(no.module)
    return nomes


def test_dominio_nao_depende_de_infraestrutura():
    violacoes = []
    for arquivo in sorted(DOMINIO.glob("*.py")):
        for nome in importacoes(arquivo):
            raiz = nome.split(".")[0]
            if raiz in PERMITIDOS or nome == INTERNOS or nome.startswith(INTERNOS + "."):
                continue
            violacoes.append(f"{arquivo.name} importa '{nome}'")
    assert not violacoes, "O dominio so pode importar a biblioteca padrao pura e o proprio dominio:\n  " + "\n  ".join(violacoes)
