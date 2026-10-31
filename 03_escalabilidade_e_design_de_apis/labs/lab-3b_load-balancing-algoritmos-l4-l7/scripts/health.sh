#!/usr/bin/env bash
# Health check ativo: derruba a instância "b" e mostra quanto tempo o balanceador leva para retirá-la.
set -u
cd "$(dirname "$0")/.."
echo ">> cerca de 3 requisicoes por segundo no round-robin (8301); aos 3 s a instancia b e parada"
( sleep 3; docker compose stop app-b >/dev/null 2>&1 ) &
for i in $(seq 1 36); do
  CODIGO="$(curl -s -o /dev/null -m 3 -w '%{http_code}' localhost:8301/)"
  printf '%s ' "$CODIGO"
  sleep 0.33
done
echo
wait
echo ">> estado no painel:"
curl -s "localhost:8399/stats;csv" | awk -F, '$1=="bk_rr" && $2 ~ /^(a|b|c)$/ {print "   servidor " $2 ": " $18}'
echo ">> para devolver a instancia: docker compose start app-b"
