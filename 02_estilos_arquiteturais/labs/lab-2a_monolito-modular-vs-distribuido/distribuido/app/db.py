"""Acesso ao banco COMPARTILHADO pelos três serviços (o mesmo esquema, as mesmas tabelas)."""
import os

import psycopg

DSN = os.environ.get("DATABASE_URL", "postgresql://luna:luna@postgres:5432/distribuido")
# Versão do esquema que este serviço espera ("status" na v1, "situacao" na v2).
COL_STATUS = "status" if os.environ.get("SCHEMA_VERSAO", "1") == "1" else "situacao"


def conectar():
    return psycopg.connect(DSN)
