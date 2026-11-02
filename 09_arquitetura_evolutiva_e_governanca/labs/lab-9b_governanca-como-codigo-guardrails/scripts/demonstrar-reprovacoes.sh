#!/usr/bin/env bash
# Mostra, de uma vez, o que cada guardrail barra: roda as verificações sobre os exemplos propositalmente ruins.
# (Cada bloco abaixo DEVE falhar; é a prova de que a regra funciona.)
set -u
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1
export PYTHONIOENCODING=utf-8
PY=""
for c in python3 python; do
  if "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
done
RAIZ="$(pwd -W 2>/dev/null || pwd)"
CONFTEST="docker run --rm -v $RAIZ:/p -w /p openpolicyagent/conftest:v0.71.1"

echo "== ADRs invalidos";                $PY scripts/verificar_adrs.py exemplos-invalidos/adrs --sem-indice
echo; echo "== Pull request sem checklist";      $PY scripts/verificar_pr.py exemplos-pr/sem-checklist.md
echo; echo "== Pull request incompleto";         $PY scripts/verificar_pr.py exemplos-pr/incompleto.md
echo; echo "== Manifests reprovados";            $CONFTEST test manifestos/reprovados -p politicas --namespace lunalog.k8s --data excecoes --no-color | cut -c1-200
echo; echo "== Dockerfile reprovado";            $CONFTEST test dockerfiles/reprovado/Dockerfile -p politicas --namespace lunalog.dockerfile --no-color
