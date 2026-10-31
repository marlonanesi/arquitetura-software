#!/bin/sh
# Cria a réplica a partir do primário (cópia inicial) e passa a segui-lo em tempo real.
set -e
export PGPASSWORD=lunalog-exemplo
if [ ! -s "$PGDATA/PG_VERSION" ]; then
  until pg_isready -h primary -U lunalog -d lunalog > /dev/null 2>&1; do sleep 1; done
  echo "standby: copiando o primário (pg_basebackup)"
  pg_basebackup -h primary -U lunalog -D "$PGDATA" -R -X stream -c fast
  chmod 700 "$PGDATA"
fi
echo "standby: seguindo o primário"
exec postgres
