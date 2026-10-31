#!/usr/bin/env bash
# Verifica as fronteiras do monólito modular com o import-linter.
#   scripts/lint.sh            roda as regras sobre o código como está
#   scripts/lint.sh --violar   injeta uma importação proibida (entregas -> internos da roteirização) e roda as regras
set -u
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1

if [ "${1:-}" = "--violar" ]; then
  rm -rf .tmp-violacao && mkdir .tmp-violacao && cp -r modular/app .tmp-violacao/app
  # um atalho "inocente": usar direto o cálculo interno da roteirização
  sed -i '1a from app.roteirizacao.calculo import calcular  # ATALHO PROIBIDO' .tmp-violacao/app/entregas/servico.py
  echo ">> Injetei em entregas/servico.py: from app.roteirizacao.calculo import calcular"
  RAIZ="$(pwd -W 2>/dev/null || pwd)/.tmp-violacao/app"
else
  RAIZ="$(pwd -W 2>/dev/null || pwd)/modular/app"
fi

docker compose run --rm --no-deps -v "$RAIZ:/srv/app" --entrypoint lint-imports monolito --no-cache
CODIGO=$?
rm -rf .tmp-violacao
exit $CODIGO
