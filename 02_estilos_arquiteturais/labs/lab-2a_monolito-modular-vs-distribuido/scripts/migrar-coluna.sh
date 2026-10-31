#!/usr/bin/env bash
# Migração "simples": renomeia a coluna entregas.status para entregas.situacao nos dois bancos.
# A partir daqui, só o código que conhece a coluna nova funciona (SCHEMA_VERSAO=2).
set -eu
cd "$(dirname "$0")/.."
for banco in modular distribuido; do
  docker compose exec -T postgres psql -U luna -d "$banco" -c "ALTER TABLE entregas RENAME COLUMN status TO situacao"
done
