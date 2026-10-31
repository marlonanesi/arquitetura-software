#!/usr/bin/env bash
# Acompanha a fila e o banco a cada 2 segundos, até a fila esvaziar (ou 120 s).
# Mostra: mensagens na fila, mensagens em processamento, linhas gravadas no banco e consumidores.
set -u
echo "tempo | na fila | em processamento | retry | dlq | gravadas no banco | consumidores"
INICIO=$(date +%s)
vazia=0
while [ $(( $(date +%s) - INICIO )) -lt 120 ]; do
  Q="$(curl -s -u guest:guest localhost:15672/api/queues/%2F/confirmacoes)"
  R="$(curl -s -u guest:guest localhost:15672/api/queues/%2F/confirmacoes.retry)"
  D="$(curl -s -u guest:guest localhost:15672/api/queues/%2F/confirmacoes.dlq)"
  campo() { echo "$1" | grep -o "\"$2\":[0-9]*" | head -1 | cut -d: -f2; }
  PRONTAS=$(campo "$Q" messages_ready); NAO_ACK=$(campo "$Q" messages_unacknowledged); CONS=$(campo "$Q" consumers)
  RETRY=$(campo "$R" messages); DLQ=$(campo "$D" messages)
  GRAVADAS=$(curl -s localhost:8401/estado | grep -o '"gravadas":[0-9]*' | cut -d: -f2)
  printf '%4ss | %7s | %16s | %5s | %3s | %17s | %s\n' $(( $(date +%s) - INICIO )) "${PRONTAS:-0}" "${NAO_ACK:-0}" "${RETRY:-0}" "${DLQ:-0}" "${GRAVADAS:-0}" "${CONS:-0}"
  if [ "${PRONTAS:-0}" = "0" ] && [ "${NAO_ACK:-0}" = "0" ] && [ "${RETRY:-0}" = "0" ] && [ $(( $(date +%s) - INICIO )) -ge 12 ]; then
    vazia=$((vazia+1)); [ $vazia -ge 2 ] && break
  else vazia=0; fi
  sleep 2
done
