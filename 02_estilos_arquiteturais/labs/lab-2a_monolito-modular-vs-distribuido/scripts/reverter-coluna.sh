#!/usr/bin/env bash
# Desfaz a migração (para repetir o cenário) e volta todo o código à versão 1 do esquema.
set -eu
cd "$(dirname "$0")/.."
for banco in modular distribuido; do
  docker compose exec -T postgres psql -U luna -d "$banco" -c "ALTER TABLE entregas RENAME COLUMN situacao TO status" 2>/dev/null || true
done
SCHEMA_VERSAO=1 SCHEMA_VERSAO_ENTREGAS=1 SCHEMA_VERSAO_ROTEIRIZACAO=1 SCHEMA_VERSAO_NOTIFICACAO=1 docker compose up -d --force-recreate monolito entregas roteirizacao notificacao
