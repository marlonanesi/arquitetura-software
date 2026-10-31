"""Adaptador de repositório em PostgreSQL (precisa do pacote psycopg)."""
from confirmacao.dominio.entrega import Entrega, Status


class RepositorioPostgres:
    def __init__(self, url: str):
        import psycopg   # importação tardia: só quem escolhe este adaptador precisa do driver

        self._conn = psycopg.connect(url, autocommit=True)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS entregas (id TEXT PRIMARY KEY, endereco TEXT NOT NULL, "
            "status TEXT NOT NULL, confirmada_em TIMESTAMPTZ)"
        )

    def salvar(self, entrega: Entrega) -> None:
        self._conn.execute(
            "INSERT INTO entregas (id, endereco, status, confirmada_em) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET endereco = EXCLUDED.endereco, status = EXCLUDED.status, "
            "confirmada_em = EXCLUDED.confirmada_em",
            (entrega.id, entrega.endereco, entrega.status.value, entrega.confirmada_em),
        )

    def obter(self, entrega_id: str) -> Entrega | None:
        linha = self._conn.execute(
            "SELECT id, endereco, status, confirmada_em FROM entregas WHERE id = %s", (entrega_id,)
        ).fetchone()
        if linha is None:
            return None
        return Entrega(id=linha[0], endereco=linha[1], status=Status(linha[2]), confirmada_em=linha[3])
