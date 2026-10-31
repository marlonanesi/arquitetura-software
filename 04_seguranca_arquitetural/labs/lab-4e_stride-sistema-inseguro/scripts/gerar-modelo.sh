#!/usr/bin/env bash
# Gera, a partir do modelo em código (modelo/modelo.py), o diagrama de fluxo de dados e o resumo de ameaças
# das duas variantes. Os arquivos vão para docs/.
set -eu
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1
for variante in inseguro seguro; do
  docker compose --profile ferramentas run --rm -T -e VARIANTE=$variante modelo sh -c "
    python modelo.py --dfd | dot -Tpng -o /docs/dfd-$variante.png &&
    python modelo.py --json /tmp/$variante.json > /dev/null &&
    python relatorio.py /tmp/$variante.json /docs/ameacas-$variante.md $variante" 2>&1 | grep -v '^ Container'
done
