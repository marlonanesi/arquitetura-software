#!/bin/sh
# Grava uma entrega a cada 0,1 s no primário e imprime cada confirmação recebida.
# O último "confirmado id=N" que aparece é o que o banco garantiu ao cliente antes do desastre.
export PGPASSWORD=lunalog-exemplo
until pg_isready -h primary -U lunalog -d lunalog > /dev/null 2>&1; do sleep 1; done
echo "escritor iniciado"
while true; do
  id=$(psql -h primary -U lunalog -d lunalog -qAt -c "INSERT INTO entregas (status) VALUES ('em_rota') RETURNING id" 2>/dev/null)
  if [ -n "$id" ]; then
    echo "$(date +%T) confirmado id=$id"
  fi
  sleep 0.1
done
