#!/usr/bin/env bash
# Simula um pull request: aplica uma mudança (opcional) e roda as quatro fitness functions,
# mostrando quais passam e quais barram o PR.
#
# Uso: bash scripts/simular.sh [acoplamento|desempenho|seguranca|compatibilidade]
# Trabalha em uma CÓPIA (.simulacao/): os arquivos originais não são alterados.
set -uo pipefail
export MSYS_NO_PATHCONV=1

mudanca=${1:-}
ORIGEM="$(cd "$(dirname "$0")/.." && pwd)"
TRAB="$ORIGEM/.simulacao"
rm -rf "$TRAB"; mkdir -p "$TRAB"
cp -r "$ORIGEM/app" "$ORIGEM/contrato" "$ORIGEM/k6" "$ORIGEM/scripts" "$TRAB/"
find "$TRAB" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null
export RAIZ="$TRAB"

if [ -n "$mudanca" ]; then
  docker run --rm -v "$TRAB":/w -w /w python:3.12-slim python scripts/mudanca.py /w "$mudanca" || exit 1
  echo "Pull request com a mudança: $mudanca"
else
  echo "Pull request sem mudança ruim."
fi
echo

falhas=0
for f in acoplamento desempenho seguranca compatibilidade; do
  ini=$(date +%s)
  saida=$(bash "$TRAB/scripts/fitness.sh" "$f" 2>&1); rc=$?
  dur=$(( $(date +%s) - ini ))
  if [ $rc -eq 0 ]; then
    printf "  %-16s PASSOU     (%ss)\n" "$f" "$dur"
  else
    printf "  %-16s FALHOU     (%ss)\n" "$f" "$dur"
    echo "$saida" | sed $'s/\[[0-9;]*m//g' | grep -E "✗|BROKEN|not allowed|^\s*- lunalog|Total:|CRITICAL|response-required|removed the|changes:|ERRO" | head -n 5 | cut -c1-150 | sed 's/^\s*/                   | /'
    falhas=$((falhas + 1))
  fi
done
echo
if [ $falhas -eq 0 ]; then echo ">>> PR LIBERADO: a arquitetura continua saudável <<<"; else echo ">>> PR BARRADO por $falhas fitness function(s) <<<"; fi
rm -rf "$TRAB"
[ $falhas -eq 0 ]
