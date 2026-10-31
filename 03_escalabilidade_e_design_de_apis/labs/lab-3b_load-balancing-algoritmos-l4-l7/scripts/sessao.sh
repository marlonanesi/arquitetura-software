#!/usr/bin/env bash
# O problema da aula 3.3: login numa instância, a requisição seguinte em outra.
# Uso: scripts/sessao.sh PORTA [assinada]
#   PORTA     8301 (round-robin) ou 8305 (round-robin com cookie de afinidade)
#   assinada  usa um token assinado (stateless) em vez de sessão guardada na instância
set -u
PORTA="${1:-8301}"
ASSINADA=0; [ "${2:-}" = "assinada" ] && ASSINADA=1
JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT

RESP="$(curl -s -c "$JAR" -b "$JAR" -X POST "localhost:$PORTA/login?assinada=$ASSINADA")"
TOKEN="$(echo "$RESP" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)"
LOGIN_EM="$(echo "$RESP" | grep -o '"instancia":"[^"]*"' | cut -d'"' -f4)"
echo "login feito na instancia '$LOGIN_EM' (tipo: $( [ $ASSINADA = 1 ] && echo token-assinado || echo sessao-local ))"

OK=0; NEGADAS=0
for i in $(seq 1 9); do
  LINHA="$(curl -s -o /dev/null -D - -c "$JAR" -b "$JAR" -H "Authorization: Bearer $TOKEN" "localhost:$PORTA/perfil")"
  CODIGO="$(echo "$LINHA" | head -1 | cut -d' ' -f2)"
  INST="$(echo "$LINHA" | grep -i '^x-instancia' | tr -d '\r' | cut -d' ' -f2)"
  echo "  /perfil #$i -> http $CODIGO (instancia $INST)"
  [ "$CODIGO" = "200" ] && OK=$((OK+1)) || NEGADAS=$((NEGADAS+1))
done
echo "resultado: $OK autenticadas, $NEGADAS negadas (401)"
