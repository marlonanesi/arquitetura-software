"""Aplica, em uma pasta de trabalho, uma mudança "ruim" que um pipeline maduro deveria barrar.

Uso: python scripts/mudanca.py <pasta> <mudanca>

Mudanças:
  teste-quebrado          altera a regra do frete, e o teste existente passa a falhar
  codigo-inseguro         adiciona um endpoint com eval() sobre entrada do usuário
  dependencia-vulneravel  fixa uma dependência com vulnerabilidade crítica conhecida
  segredo-no-codigo       coloca uma credencial no código
  falha-so-em-producao    a aplicação passa a exigir uma configuração que só falta em produção
"""
import sys
from pathlib import Path

pasta = Path(sys.argv[1])
nome = sys.argv[2]


def trocar(arquivo: str, antigo: str, novo: str):
    p = pasta / arquivo
    texto = p.read_text(encoding="utf-8")
    assert antigo in texto, f"trecho não encontrado em {arquivo}"
    p.write_text(texto.replace(antigo, novo, 1), encoding="utf-8")


def acrescentar(arquivo: str, trecho: str):
    p = pasta / arquivo
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\n" + trecho, encoding="utf-8")


if nome == "teste-quebrado":
    # Um "ajuste" na taxa fixa que ninguém atualizou nos testes.
    trocar("app/main.py", "return round(8.0 + peso_kg", "return round(9.5 + peso_kg")

elif nome == "codigo-inseguro":
    acrescentar("app/main.py", '''

@app.get("/calcular")
def calcular(expressao: str):
    # CUIDADO: eval() sobre entrada do usuário permite execução remota de código.
    return {"resultado": eval(expressao)}
''')

elif nome == "dependencia-vulneravel":
    acrescentar("app/requirements.txt", "pyyaml==5.3.1\n")

elif nome == "segredo-no-codigo":
    # O valor é montado aqui, em tempo de execução, para este script não ser ele mesmo
    # detectado como "segredo no repositório". É um valor fictício, de exemplo.
    import hashlib
    token = hashlib.sha256(b"token-de-exemplo-do-lab").hexdigest()
    trocar("app/main.py", 'VERSAO = os.environ.get("VERSAO", "dev")',
           f'VERSAO = os.environ.get("VERSAO", "dev")\nTOKEN_DO_REGISTRY = "{token}"')

elif nome == "falha-so-em-producao":
    trocar("app/main.py", 'VERSAO = os.environ.get("VERSAO", "dev")',
           'VERSAO = os.environ.get("VERSAO", "dev")\n'
           'if os.environ.get("AMBIENTE") == "producao" and "URL_DO_CACHE" not in os.environ:\n'
           '    raise RuntimeError("URL_DO_CACHE ausente em producao")')

else:
    sys.exit(f"mudança desconhecida: {nome}")

print(f"mudança aplicada: {nome}")
