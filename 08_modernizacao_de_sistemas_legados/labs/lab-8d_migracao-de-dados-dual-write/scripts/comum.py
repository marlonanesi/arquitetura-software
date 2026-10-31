"""Funções compartilhadas pelos scripts de migração."""
import os
import sys

import psycopg

sys.path.insert(0, "/app")
import traducao  # noqa: E402

URL_LEGADO = os.environ.get("URL_LEGADO", "postgresql://luna:luna@postgres:5432/legado")
URL_NOVO = os.environ.get("URL_NOVO", "postgresql://luna:luna@postgres:5432/novo")

UPSERT_NOVO = (
    "INSERT INTO entregas (id, status, previsao, valor_centavos, transportadora_id, origem) VALUES (%s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, previsao = EXCLUDED.previsao, valor_centavos = EXCLUDED.valor_centavos, "
    "transportadora_id = EXCLUDED.transportadora_id, origem = EXCLUDED.origem, atualizado_em = now() "
    "WHERE entregas.origem <> 'novo-primario'"          # depois do cutover da escrita, o novo é a verdade: não sobrescrever
)
UPSERT_QUARENTENA = ("INSERT INTO quarentena (id, motivo, bruto) VALUES (%s, %s, %s::jsonb) "
                     "ON CONFLICT (id) DO UPDATE SET motivo = EXCLUDED.motivo, bruto = EXCLUDED.bruto, em = now()")


def legado():
    return psycopg.connect(URL_LEGADO)


def novo():
    return psycopg.connect(URL_NOVO)


def ler_legado_traduzido(c):
    """Lê todo o legado. Devolve (válidas: {id: dict}, inválidas: {id: motivo})."""
    validas, invalidas = {}, {}
    for cod, st, dt, vlr, transp in c.execute("SELECT cod_ent, st, dt_prev, vlr, transp FROM entrega_tb ORDER BY cod_ent"):
        try:
            validas[cod] = traducao.do_legado(cod, st, dt, vlr, transp)
        except traducao.ErroDeTraducao as erro:
            invalidas[cod] = str(erro)
    return validas, invalidas


def ler_novo(c):
    return {l[0]: {"id": l[0], "status": l[1], "previsao": l[2], "valor_centavos": l[3], "transportadora_id": l[4]}
            for l in c.execute("SELECT id, status, previsao, valor_centavos, transportadora_id FROM entregas")}


def bucket(cod: str) -> int:
    return int(cod.split("-")[1]) // 1000
