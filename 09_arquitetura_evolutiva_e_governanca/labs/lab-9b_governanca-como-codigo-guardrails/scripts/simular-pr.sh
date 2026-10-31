#!/usr/bin/env bash
# Simula um pull request: o desenvolvedor adiciona um manifest em manifestos/novo/ e os guardrails rodam.
#   scripts/simular-pr.sh ruim    adiciona um manifest com problemas (o CI reprova)
#   scripts/simular-pr.sh bom     adiciona um manifest conforme (o CI aprova)
# Ao final, o arquivo adicionado é removido, para o lab continuar limpo.
set -u
cd "$(dirname "$0")/.."
ORIGEM="manifestos/reprovados/varios-problemas.yaml"
[ "${1:-ruim}" = "bom" ] && ORIGEM="manifestos/aprovados/roteirizacao.yaml"
DESTINO="manifestos/novo/proposta.yaml"
cp "$ORIGEM" "$DESTINO"
echo ">> o desenvolvedor adiciona $DESTINO (copia de $ORIGEM)"
bash scripts/verificar.sh
CODIGO=$?
rm -f "$DESTINO"
echo ">> (arquivo de simulacao removido)"
exit $CODIGO
