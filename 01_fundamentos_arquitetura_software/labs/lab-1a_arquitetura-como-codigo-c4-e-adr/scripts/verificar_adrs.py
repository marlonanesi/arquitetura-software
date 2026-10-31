#!/usr/bin/env python3
"""Valida os ADRs do repositório e gera o índice (INDICE_ADRS.md).

Regras (as que um revisor checaria à mão em cada pull request):
  - nome do arquivo: NNNN-titulo-em-minusculas.md, com número único
  - front matter com status, date (AAAA-MM-DD) e decision-makers
  - status em: proposed, accepted, rejected, deprecated, superseded by ADR-NNNN
  - título "# NNNN. ..." com o mesmo número do arquivo
  - seções obrigatórias: Contexto e problema, Decisão, Consequências
  - um ADR "superseded by ADR-NNNN" aponta para um ADR que existe e que o menciona

Uso: python scripts/verificar_adrs.py [pasta_dos_adrs]    (padrão: adrs)
Saída: código 0 se tudo certo, 1 se houver problemas.
"""
import re
import sys
from datetime import date
from pathlib import Path

PASTA = Path(sys.argv[1] if len(sys.argv) > 1 else "adrs")
STATUS_FIXOS = {"proposed", "accepted", "rejected", "deprecated"}
SECOES = ["Contexto e problema", "Decisão", "Consequências"]
NOME = re.compile(r"^(\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.md$")
SUBSTITUIDO = re.compile(r"^superseded by ADR-(\d{4})$")


def ler(caminho: Path):
    texto = caminho.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", texto, re.S)
    if not m:
        return None, texto
    campos = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            chave, valor = linha.split(":", 1)
            campos[chave.strip()] = valor.strip()
    return campos, m.group(2)


def main() -> int:
    erros: list[str] = []
    adrs: dict[str, dict] = {}

    for caminho in sorted(PASTA.rglob("*.md")):
        rel = caminho.relative_to(PASTA).as_posix()
        m = NOME.match(caminho.name)
        if not m:
            erros.append(f"{rel}: nome fora do padrão NNNN-titulo-em-minusculas.md")
            continue
        numero = m.group(1)
        if numero in adrs:
            erros.append(f"{rel}: número {numero} repetido ({adrs[numero]['rel']})")
            continue

        campos, corpo = ler(caminho)
        if campos is None:
            erros.append(f"{rel}: sem front matter (--- status, date, decision-makers ---)")
            continue
        for chave in ("status", "date", "decision-makers"):
            if not campos.get(chave):
                erros.append(f"{rel}: falta o campo '{chave}' no front matter")
        status = campos.get("status", "")
        if status and status not in STATUS_FIXOS and not SUBSTITUIDO.match(status):
            erros.append(f"{rel}: status inválido '{status}' (use proposed, accepted, rejected, deprecated ou superseded by ADR-NNNN)")
        try:
            date.fromisoformat(campos.get("date", ""))
        except ValueError:
            erros.append(f"{rel}: data inválida '{campos.get('date', '')}' (use AAAA-MM-DD)")

        titulo = re.search(r"^# (\d{4})\. (.+)$", corpo, re.M)
        if not titulo:
            erros.append(f"{rel}: título deve ser '# {numero}. Título da decisão'")
            nome_titulo = caminho.stem
        else:
            nome_titulo = titulo.group(2)
            if titulo.group(1) != numero:
                erros.append(f"{rel}: o número do título ({titulo.group(1)}) difere do arquivo ({numero})")
        for secao in SECOES:
            if not re.search(rf"^## {re.escape(secao)}\s*$", corpo, re.M):
                erros.append(f"{rel}: falta a seção '## {secao}'")

        adrs[numero] = {"rel": rel, "status": status, "data": campos.get("date", ""),
                        "titulo": nome_titulo, "corpo": corpo}

    for numero, adr in adrs.items():
        m = SUBSTITUIDO.match(adr["status"])
        if not m:
            continue
        sucessor = m.group(1)
        if sucessor not in adrs:
            erros.append(f"{adr['rel']}: substituído por ADR-{sucessor}, que não existe")
        elif numero not in adrs[sucessor]["corpo"]:
            erros.append(f"{adrs[sucessor]['rel']}: deveria mencionar que substitui o ADR {numero}")

    if erros:
        print(f"{len(erros)} problema(s) nos ADRs:")
        for e in erros:
            print(f"  - {e}")
        return 1

    linhas = ["# Índice dos ADRs", "",
              "> Gerado por `scripts/verificar_adrs.py`. Não edite à mão.", "",
              "| ADR | Decisão | Status | Data |", "|---|---|---|---|"]
    for numero in sorted(adrs):
        a = adrs[numero]
        linhas.append(f"| {numero} | [{a['titulo']}]({PASTA.as_posix()}/{a['rel']}) | {a['status']} | {a['data']} |")
    Path("INDICE_ADRS.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{len(adrs)} ADRs válidos. Índice gravado em INDICE_ADRS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
