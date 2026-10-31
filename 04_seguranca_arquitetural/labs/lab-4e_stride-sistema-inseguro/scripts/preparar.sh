#!/usr/bin/env bash
# Gera o segredo do JWT da versão segura em um arquivo .env (ignorado pelo Git). Roda uma vez.
# O segredo é aleatório e NUNCA entra no código: é exatamente o que a falha F1 não fazia.
set -eu
cd "$(dirname "$0")/.."
if [ -f .env ] && grep -q '^JWT_SECRET=' .env; then
  echo ".env ja existe; mantendo o segredo atual."
  exit 0
fi
SEGREDO="$( (openssl rand -hex 32 2>/dev/null) || (python3 -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null) || (python -c 'import secrets; print(secrets.token_hex(32))') )"
printf 'JWT_SECRET=%s\n' "$SEGREDO" > .env
echo ".env criado com um segredo aleatorio."
