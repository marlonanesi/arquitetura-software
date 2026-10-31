"""Gera um repositório Git de demonstração com um ano de histórico, para o lab de hotspots.

O histórico tem padrões plantados de propósito, que a análise precisa descobrir:

  src/precificacao.py   muito alterado E muito complexo       -> o HOTSPOT principal (e quase só o Roberto mexe)
  src/roteirizacao.py   muito alterado E complexo             -> segundo hotspot
  src/notificacao.py    muito complexo, mas quase nunca muda  -> "complexo e quieto": não é prioridade
  src/constantes.py     muito alterado, mas trivial           -> "agitado e simples": configuração
  src/faturamento.py e src/impostos.py   mudam sempre juntos, sem se importar  -> acoplamento temporal oculto

Uso: python gerar_repositorio.py [pasta]     (padrão: /dados/repo-demo)
"""
import os
import random
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(sys.argv[1] if len(sys.argv) > 1 else "/dados/repo-demo")
random.seed(42)

AUTORES = {
    "Roberto": "roberto@lunalog.example", "Ana": "ana@lunalog.example", "Camila": "camila@lunalog.example",
    "Diego": "diego@lunalog.example", "Eva": "eva@lunalog.example",
}


def git(*args, env=None):
    subprocess.run(["git", *args], cwd=RAIZ, check=True, capture_output=True, env={**os.environ, **(env or {})})


def funcao_com_ramos(nome: str, ramos: int, parametros="valor, regiao") -> str:
    """Uma função com 'ramos' desvios (complexidade ciclomática = ramos + 1) e um marcador para crescer depois."""
    linhas = [f"def {nome}({parametros}):"]
    for i in range(ramos):
        palavra = "if" if i == 0 else "elif"
        linhas.append(f'    {palavra} regiao == "R{i:02d}":')
        linhas.append(f"        return valor * {1 + i / 100:.2f}")
    linhas.append("    # <ramos>")
    linhas.append("    return valor")
    return "\n".join(linhas) + "\n"


def adicionar_ramo(conteudo: str) -> str:
    """Faz o arquivo crescer em complexidade: acrescenta mais um desvio antes do marcador."""
    n = conteudo.count('regiao == "R')
    novo = f'    elif regiao == "R{n:02d}":\n        return valor * {1 + n / 100:.2f}\n    # <ramos>'
    return conteudo.replace("    # <ramos>", novo, 1)


def tocar(conteudo: str, indice: int) -> str:
    """Uma alteração pequena: atualiza o comentário de revisão (gera churn sem mudar a complexidade)."""
    linhas = conteudo.split("\n")
    marca = f"# revisao {indice}"
    if linhas[0].startswith("# revisao"):
        linhas[0] = marca
    else:
        linhas.insert(0, marca)
    return "\n".join(linhas)


# ---- estado inicial do repositório ----------------------------------------------------------------
ARQUIVOS = {
    "src/precificacao.py": funcao_com_ramos("calcular_preco", 22) + "\n" + funcao_com_ramos("calcular_desconto", 8),
    "src/roteirizacao.py": funcao_com_ramos("escolher_rota", 16) + "\n" + funcao_com_ramos("agrupar_paradas", 6),
    "src/notificacao.py": funcao_com_ramos("montar_mensagem", 30) + "\n" + funcao_com_ramos("escolher_canal", 10),
    "src/constantes.py": "TAXA_BASE = 1.0\nLIMITE_PESO = 30\nPRAZO_PADRAO = 5\n",
    "src/clientes.py": funcao_com_ramos("classificar_cliente", 4),
    "src/relatorios.py": funcao_com_ramos("resumo_mensal", 5),
    "src/faturamento.py": funcao_com_ramos("faturar", 6),
    "src/impostos.py": funcao_com_ramos("calcular_imposto", 6),
    "tests/test_precificacao.py": "def test_preco():\n    assert True\n",
    "README.md": "# LunaLog (demonstracao)\n",
}


def escrever(caminho: str, conteudo: str):
    destino = RAIZ / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")
    ARQUIVOS[caminho] = conteudo


def commitar(mensagem: str, autor: str, quando: datetime):
    git("add", "-A")
    data = quando.strftime("%Y-%m-%dT%H:%M:%S")
    git("commit", "-q", "-m", mensagem, env={
        "GIT_AUTHOR_NAME": autor, "GIT_AUTHOR_EMAIL": AUTORES[autor], "GIT_AUTHOR_DATE": data,
        "GIT_COMMITTER_NAME": autor, "GIT_COMMITTER_EMAIL": AUTORES[autor], "GIT_COMMITTER_DATE": data})


if RAIZ.exists():
    shutil.rmtree(RAIZ)
RAIZ.mkdir(parents=True)
git("init", "-q", "-b", "main")

inicio = datetime(2025, 11, 3, 9, 0)
for caminho, conteudo in ARQUIVOS.copy().items():
    escrever(caminho, conteudo)
commitar("Versao inicial", "Roberto", inicio)

# (tipo de commit, peso, arquivos que ele altera, quem costuma fazer)
TIPOS = [
    ("preco", 17, ["src/precificacao.py"], ["Roberto"] * 8 + ["Ana"] * 2),
    ("rota", 13, ["src/roteirizacao.py"], ["Ana", "Camila", "Diego"]),
    ("fatura", 18, ["src/faturamento.py", "src/impostos.py"], ["Camila", "Diego", "Eva"]),
    ("config", 15, ["src/constantes.py"], list(AUTORES)),
    ("cliente", 8, ["src/clientes.py"], ["Eva", "Diego"]),
    ("relatorio", 6, ["src/relatorios.py"], ["Eva", "Ana"]),
    ("teste", 5, ["tests/test_precificacao.py"], ["Roberto", "Ana"]),
    ("doc", 3, ["README.md"], list(AUTORES)),
]
pesos = [t[1] for t in TIPOS]

# Probabilidade de cada alteração acrescentar um desvio (complexidade) ao arquivo
CRESCIMENTO = {"src/precificacao.py": 0.7, "src/roteirizacao.py": 0.6, "src/faturamento.py": 0.05,
               "src/impostos.py": 0.05, "src/clientes.py": 0.08, "src/relatorios.py": 0.08}

quando = inicio
for numero in range(1, 421):
    quando += timedelta(hours=random.randint(8, 32))
    tipo, _, arquivos, autores = random.choices(TIPOS, weights=pesos)[0]
    for caminho in arquivos:
        conteudo = ARQUIVOS[caminho]
        if "# <ramos>" in conteudo and random.random() < CRESCIMENTO.get(caminho, 0):
            conteudo = adicionar_ramo(conteudo)       # a complexidade cresce com o tempo, onde o time mais mexe
        conteudo = tocar(conteudo, numero)
        escrever(caminho, conteudo)
    commitar(f"{tipo}: alteracao {numero}", random.choice(autores), quando)
    if numero in (12, 25, 38):      # o arquivo complexo e quieto muda só 3 vezes, bem no começo, em ordem cronológica
        escrever("src/notificacao.py", adicionar_ramo(tocar(ARQUIVOS["src/notificacao.py"], 9000 + numero)))
        commitar(f"notificacao: ajuste {numero}", "Camila", quando + timedelta(minutes=5))

print(f"repositorio de demonstracao criado em {RAIZ}")
print(subprocess.run(["git", "log", "--oneline"], cwd=RAIZ, capture_output=True, text=True).stdout.count("\n"), "commits")
