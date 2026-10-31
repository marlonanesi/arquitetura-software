"""Operador de flags: lê e altera o arquivo de flags que o flagd observa (volume compartilhado em /flags).

  python flags.py mostrar
  python flags.py leitura 5          liberação da leitura para 5% dos usuários (0 desliga a liberação)
  python flags.py sombra on|off
  python flags.py escrita legado|dupla|novo
  python flags.py kill on|off        o botão de emergência: tudo volta ao legado

Em produção, estas flags viveriam em um serviço de feature flags (LaunchDarkly, Unleash, flagd com Git como
fonte), com revisão, auditoria e permissões. Aqui um arquivo basta para ver o mecanismo.
"""
import json
import sys
from pathlib import Path

ARQUIVO = Path("/flags/flags.json")


def carregar() -> dict:
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))


def salvar(dados: dict) -> None:
    ARQUIVO.write_text(json.dumps(dados, indent=2), encoding="utf-8")      # uma escrita só: o flagd recarrega


def percentual_leitura(dados: dict) -> int:
    alvo = dados["flags"]["leitura-novo"].get("targeting", {}).get("fractional")
    return next((p for nome, p in alvo if nome == "novo"), 0) if alvo else 0


def definir_leitura(pct: int) -> None:
    dados = carregar()
    flag = dados["flags"]["leitura-novo"]
    if pct <= 0:
        flag.pop("targeting", None)
    else:
        flag["targeting"] = {"fractional": [["novo", pct], ["legado", 100 - pct]] if pct < 100 else [["novo", 100]]}
    salvar(dados)


def definir_variante(chave: str, variante: str) -> None:
    dados = carregar()
    dados["flags"][chave]["defaultVariant"] = variante
    salvar(dados)


def estado() -> dict:
    d = carregar()["flags"]
    return {"leitura_novo_pct": percentual_leitura(carregar()), "sombra": d["sombra"]["defaultVariant"],
            "escrita": d["escrita"]["defaultVariant"], "kill_switch_novo": d["kill-switch-novo"]["defaultVariant"]}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "mostrar":
        pass
    elif a[0] == "leitura":
        definir_leitura(int(a[1]))
    elif a[0] == "sombra":
        definir_variante("sombra", "ligada" if a[1] == "on" else "desligada")
    elif a[0] == "escrita":
        definir_variante("escrita", a[1])
    elif a[0] == "kill":
        definir_variante("kill-switch-novo", "ligado" if a[1] == "on" else "desligado")
    else:
        sys.exit(__doc__)
    print(json.dumps(estado(), ensure_ascii=False))
