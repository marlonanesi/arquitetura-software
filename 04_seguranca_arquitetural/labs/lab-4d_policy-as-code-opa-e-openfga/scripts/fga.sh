#!/usr/bin/env bash
# Atalho para a CLI do OpenFGA: descobre sozinho a loja "lunalog" e a passa como --store-id.
# Exemplos:
#   scripts/fga.sh tuple write usuario:ana operador filial:rapido-rj
#   scripts/fga.sh query check usuario:ana viewer rota:R2
#   scripts/fga.sh query list-objects usuario:dora viewer rota
#   scripts/fga.sh tuple delete usuario:ana operador filial:rapido-rj
set -eu
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1
FGA="docker compose --profile ferramentas run --rm -T fga"
STORE="$($FGA store list 2>/dev/null | tr ',' '\n' | grep -B1 -A0 '"name":"lunalog"' | grep -o '"id":"[^"]*"' | tail -1 | cut -d'"' -f4)"
[ -n "$STORE" ] || STORE="$($FGA store list 2>/dev/null | grep -o '"id": *"[^"]*"' | head -1 | cut -d'"' -f4)"
GRUPO="$1"; SUB="$2"; shift 2
$FGA "$GRUPO" "$SUB" --store-id "$STORE" "$@" 2>&1 | grep -v "^ Container"
