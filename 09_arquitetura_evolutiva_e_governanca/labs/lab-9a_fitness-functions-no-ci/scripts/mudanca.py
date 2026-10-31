"""Aplica, em uma pasta de trabalho, uma mudança que degrada a arquitetura de uma forma específica.

Uso: python scripts/mudanca.py <pasta> <mudanca>

Mudanças (cada uma deve ser barrada por UMA fitness function):
  acoplamento      o domínio de tarifas passa a importar o domínio de clientes
  desempenho       um cálculo passa a levar 400 ms
  seguranca        uma dependência com vulnerabilidade crítica conhecida entra no projeto
  compatibilidade  o campo "frete" da resposta é renomeado para "valor_frete"
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


if nome == "acoplamento":
    # "Só um atalho": tarifas passa a consultar o cadastro de clientes direto.
    trocar("app/lunalog/dominio/tarifas.py", "from lunalog.infra import repositorio",
           "from lunalog.dominio import clientes\nfrom lunalog.infra import repositorio")
    trocar("app/lunalog/dominio/tarifas.py", "    return round(",
           "    clientes.buscar_cliente('C-1')  # atalho: dependência nova entre domínios\n    return round(")

elif nome == "desempenho":
    trocar("app/lunalog/dominio/tarifas.py", "from lunalog.infra import repositorio",
           "import time\n\nfrom lunalog.infra import repositorio")
    trocar("app/lunalog/dominio/tarifas.py", "    return round(",
           "    time.sleep(0.4)  # consulta lenta que ninguém mediu\n    return round(")

elif nome == "seguranca":
    p = pasta / "app/requirements.txt"
    p.write_text(p.read_text(encoding="utf-8").rstrip("\n") + "\npyyaml==5.3.1\n", encoding="utf-8")

elif nome == "compatibilidade":
    trocar("app/lunalog/api/rotas.py", "class Frete(BaseModel):\n    frete: float", "class Frete(BaseModel):\n    valor_frete: float")
    trocar("app/lunalog/api/rotas.py", "Frete(frete=tarifas.calcular_frete", "Frete(valor_frete=tarifas.calcular_frete")

else:
    sys.exit(f"mudança desconhecida: {nome}")

print(f"mudança aplicada: {nome}")
