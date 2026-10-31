#!/usr/bin/env bash
# Os guardrails de governança, na ordem em que rodam no CI de cada pull request.
# Precisa de Docker (Conftest) e Python 3.
#   scripts/verificar.sh                     verifica o conteúdo do repositório
#   scripts/verificar.sh corpo-do-pr.md      e confere também o checklist do pull request
set -u
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1
export PYTHONIOENCODING=utf-8

PY=""
for c in python3 python; do
  if "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Python 3 nao encontrado"; exit 1; }
RAIZ="$(pwd -W 2>/dev/null || pwd)"
CONFTEST="docker run --rm -v $RAIZ:/p -w /p openpolicyagent/conftest:latest"
FALHAS=0
etapa() { echo; echo "== $1"; }
passo() { "$@" || FALHAS=$((FALHAS+1)); }

etapa "1. ADRs: formato, status, responsaveis e substituicoes"
passo $PY scripts/verificar_adrs.py adrs --sem-indice

etapa "2. CODEOWNERS: toda area tem dono; areas criticas tem dois"
passo $PY scripts/verificar_codeowners.py CODEOWNERS

if [ "${1:-}" != "" ]; then
  etapa "3. Pull request: checklist arquitetural"
  passo $PY scripts/verificar_pr.py "$1"
fi

etapa "4. Politicas: testes unitarios das proprias regras"
passo $CONFTEST verify -p politicas --no-color

etapa "5. Manifests do Kubernetes (manifestos/aprovados e manifestos/novo)"
passo $CONFTEST test manifestos/aprovados manifestos/novo -p politicas --namespace lunalog.k8s --data excecoes --no-color

etapa "6. Dockerfiles"
passo $CONFTEST test dockerfiles/aprovado/Dockerfile -p politicas --namespace lunalog.dockerfile --no-color

echo
if [ $FALHAS -gt 0 ]; then
  echo "RESULTADO: $FALHAS etapa(s) reprovada(s). O merge fica bloqueado."
  exit 1
fi
echo "RESULTADO: todos os guardrails passaram."
