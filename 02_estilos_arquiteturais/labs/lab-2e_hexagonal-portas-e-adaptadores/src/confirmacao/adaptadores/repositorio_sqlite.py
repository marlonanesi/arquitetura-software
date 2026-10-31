"""Adaptador de repositório em SQLite (um arquivo, sem servidor)."""
import sqlite3
from datetime import datetime

from confirmacao.dominio.entrega import Entrega, Status


class RepositorioSqlite:
    def __init__(self, caminho: str):
        self._conn = sqlite3.connect(caminho)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS entregas (id TEXT PRIMARY KEY, endereco TEXT NOT NULL, "
            "status TEXT NOT NULL, confirmada_em TEXT)"
        )
        self._conn.commit()

    def salvar(self, entrega: Entrega) -> None:
        self._conn.execute(
            "INSERT INTO entregas (id, endereco, status, confirmada_em) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET endereco = excluded.endereco, status = excluded.status, "
            "confirmada_em = excluded.confirmada_em",
            (entrega.id, entrega.endereco, entrega.status.value,
             entrega.confirmada_em.isoformat() if entrega.confirmada_em else None),
        )
        self._conn.commit()

    def obter(self, entrega_id: str) -> Entrega | None:
        linha = self._conn.execute(
            "SELECT id, endereco, status, confirmada_em FROM entregas WHERE id = ?", (entrega_id,)
        ).fetchone()
        if linha is None:
            return None
        return Entrega(id=linha[0], endereco=linha[1], status=Status(linha[2]),
                       confirmada_em=datetime.fromisoformat(linha[3]) if linha[3] else None)
