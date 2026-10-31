#!/bin/sh
# Permite que a réplica (outro contêiner) se conecte para replicar.
echo "host replication all all scram-sha-256" >> "$PGDATA/pg_hba.conf"
