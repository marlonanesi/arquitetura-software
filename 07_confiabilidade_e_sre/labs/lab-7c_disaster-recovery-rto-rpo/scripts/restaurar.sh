#!/bin/sh
# Restaura o banco a partir do backup base + WAL arquivado (point-in-time recovery) e mede o RTO.
set -e
inicio=$(date +%s)

echo "restaurar: copiando o backup base"
rm -rf "$PGDATA"/* "$PGDATA"/.[!.]* 2>/dev/null || true
cp -a /backups/base/. "$PGDATA"/
chmod 700 "$PGDATA"

# O arquivo recovery.signal manda o PostgreSQL iniciar em modo de recuperação.
touch "$PGDATA/recovery.signal"
echo "restore_command = 'cp /arquivo/%f %p'" >> "$PGDATA/postgresql.auto.conf"
if [ -n "$ALVO" ]; then
  echo "recovery_target_time = '$ALVO'" >> "$PGDATA/postgresql.auto.conf"
  echo "recovery_target_action = 'promote'" >> "$PGDATA/postgresql.auto.conf"
  echo "restaurar: alvo = $ALVO"
else
  echo "restaurar: sem alvo, reproduzindo todo o WAL arquivado"
fi

postgres &
PID=$!

# Espera a recuperação terminar (o banco deixa de estar em modo de recuperação).
until [ "$(psql -U lunalog -d lunalog -At -c 'SELECT pg_is_in_recovery()' 2>/dev/null)" = "f" ]; do sleep 0.5; done
fim=$(date +%s)
echo "restaurar: PRONTO. RTO medido (copia + reproducao do WAL) = $((fim - inicio)) segundos"
wait $PID
