"""O event store sobre PostgreSQL: acrescentar eventos e ler um fluxo."""
import json
import os

import psycopg

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://luna:luna@postgres:5432/eventos")


class ConflitoDeVersao(Exception):
    pass


def conectar():
    return psycopg.connect(DATABASE_URL, autocommit=True)


def ler_fluxo(c, agregado_id: str, ate: str | None = None) -> list[dict]:
    """Todos os eventos de um agregado, em ordem; com 'ate', só os que ocorreram até aquele instante."""
    consulta = "SELECT tipo, esquema, dados, ator, ocorrido_em FROM eventos WHERE agregado_id = %s"
    params: list = [agregado_id]
    if ate:
        consulta += " AND ocorrido_em <= %s::timestamptz"
        params.append(ate)
    linhas = c.execute(consulta + " ORDER BY versao", params).fetchall()
    return [{"tipo": t, "esquema": s, "dados": d, "ator": a, "ocorrido_em": o} for t, s, d, a, o in linhas]


def acrescentar(c, agregado_id: str, versao_atual: int, eventos: list[dict]) -> None:
    """Acrescenta eventos com controle otimista: se alguém gravou antes, a versão colide e nada é gravado."""
    try:
        with c.transaction():
            for i, e in enumerate(eventos, 1):
                c.execute("INSERT INTO eventos (agregado_id, versao, tipo, esquema, dados, ator) VALUES (%s, %s, %s, %s, %s::jsonb, %s)",
                          (agregado_id, versao_atual + i, e["tipo"], e["esquema"], json.dumps(e["dados"]), e["ator"]))
    except psycopg.errors.UniqueViolation:
        raise ConflitoDeVersao(f"o agregado {agregado_id} mudou desde a versao {versao_atual}")
