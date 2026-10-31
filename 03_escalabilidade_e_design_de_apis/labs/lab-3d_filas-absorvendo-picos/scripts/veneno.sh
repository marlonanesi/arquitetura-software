#!/usr/bin/env bash
# Envia 3 mensagens "venenosas" (que nunca podem ser processadas) para a fila.
# O worker tenta 3 vezes, com 2 s de espera entre as tentativas, e as manda para a DLQ.
for i in 1 2 3; do
  curl -s -X POST localhost:8401/confirmacoes/fila -H 'Content-Type: application/json' -d "{\"codigo\":\"VENENO-$i\"}"; echo
done
