"""A matriz de acesso: quem vê o quê, em cada modelo, contra a regra de negócio correta.

Para cada usuário e cada rota/entrega, pergunta ao serviço (que pergunta ao PDP) e compara com o
GABARITO, a regra escrita em português:
  - o motorista vê apenas as rotas atribuídas a ele
  - o operador vê as rotas da sua filial
  - o gerente vê as rotas de todas as filiais da sua transportadora
  - o auditor da plataforma vê tudo
  - ninguém vê dados de outra transportadora
Uma entrega tem a mesma visibilidade da rota a que pertence.

Uso: python matriz.py [rbac|abac|rebac ...]   (padrão: os três)   |   HORA=23 python matriz.py abac
"""
import os
import sys

import httpx

ROTAS = os.environ.get("ROTAS", "http://localhost:8611")
ENTREGAS = os.environ.get("ENTREGAS", "http://localhost:8612")
HORA = int(os.environ.get("HORA", "10"))

USUARIOS = ["ana", "bruno", "carla", "dora", "eva", "fabio", "gil"]
RECURSOS = [("rotas", "R1"), ("rotas", "R2"), ("rotas", "R3"), ("entregas", "E1"), ("entregas", "E2"), ("entregas", "E3")]

# Gabarito (a regra de negócio, em dados)
VISIVEL = {
    "ana": {"R1", "E1"},                                   # operadora da filial rapido-sp (em horário comercial)
    "bruno": {"R1", "E1"},
    "carla": {"R3", "E3"},
    "dora": {"R1", "R2", "E1", "E2"},                      # gerente da transportadora rapido
    "eva": {"R1", "R2", "R3", "E1", "E2", "E3"},           # auditora da plataforma
    "fabio": {"R2", "E2"},
    "gil": {"R3", "E3"},                                   # gerente da transportadora veloz
}
if HORA >= 22 or HORA < 6:
    VISIVEL["ana"] = set()                                 # operador fora do horário comercial

cliente = httpx.Client(timeout=10)


def consultar(pdp: str, usuario: str, servico: str, rid: str) -> int:
    base = ROTAS if servico == "rotas" else ENTREGAS
    return cliente.get(f"{base}/{servico}/{rid}", params={"pdp": pdp},
                       headers={"X-Usuario": usuario, "X-Hora": str(HORA)}).status_code


def matriz(pdp: str) -> int:
    erros = []
    print(f"\n=== {pdp.upper()} (hora {HORA}h) ===")
    print(f"{'':<7}" + "".join(f"{r:>5}" for _, r in RECURSOS))
    for usuario in USUARIOS:
        linha = f"{usuario:<7}"
        for servico, rid in RECURSOS:
            codigo = consultar(pdp, usuario, servico, rid)
            permitido = codigo == 200
            esperado = rid in VISIVEL[usuario]
            if codigo not in (200, 403):
                marca = "ERR"
            elif permitido == esperado:
                marca = "sim" if permitido else "nao"
            else:
                marca = "VAZA" if permitido else "FALTA"
                erros.append(f"{usuario} -> {rid}: {'permitiu' if permitido else 'negou'}, mas deveria {'negar' if permitido else 'permitir'}")
            linha += f"{marca:>5}"
        print(linha)
    total = len(USUARIOS) * len(RECURSOS)
    print(f"decisoes erradas: {len(erros)} de {total}")
    for e in erros[:6]:
        print(f"  - {e}")
    if len(erros) > 6:
        print(f"  ... e mais {len(erros) - 6}")
    return len(erros)


if __name__ == "__main__":
    modelos = sys.argv[1:] or ["rbac", "abac", "rebac"]
    for m in modelos:
        matriz(m)
    print("\nLegenda: sim/nao = decisao correta; VAZA = acesso indevido concedido; FALTA = acesso devido negado")
