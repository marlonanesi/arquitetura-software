"""Acesso ao banco e controle de transação, compartilhados pelos módulos."""
import os
from contextlib import contextmanager

import psycopg

DSN = os.environ.get("DATABASE_URL", "postgresql://luna:luna@postgres:5432/modular")
# Versão do esquema que este código espera ("status" na v1, "situacao" na v2).
COL_STATUS = "status" if os.environ.get("SCHEMA_VERSAO", "1") == "1" else "situacao"


@contextmanager
def transacao():
    """Uma única transação para o caso de uso inteiro: ou tudo grava, ou nada grava."""
    with psycopg.connect(DSN) as conn:   # o "with" faz commit na saída normal e rollback em exceção
        yield conn
