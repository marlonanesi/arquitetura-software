"""Backfill: copia o histórico do banco legado para o novo, em lotes, de forma idempotente.

  python backfill.py            cópia completa
  python backfill.py --delta    copia só o que mudou desde a última execução (dt_alt)

Características de um backfill seguro:
  - em LOTES, com ponto de retomada (a chave do último registro copiado)
  - IDEMPOTENTE: rodar de novo não duplica nem estraga (upsert)
  - o que não pode ser traduzido vai para a QUARENTENA, com o motivo; nada some em silêncio
  - não bloqueia o legado: só lê, e o legado segue recebendo escritas
"""
import json
import sys
import time

import comum
import traducao

TAMANHO_LOTE = 1000
delta = "--delta" in sys.argv

with comum.legado() as cl, comum.novo() as cn:
    inicio_agora = cl.execute("SELECT now()").fetchone()[0]
    desde = None
    if delta:
        linha = cn.execute("SELECT valor FROM controle WHERE chave = 'backfill_inicio'").fetchone()
        if linha is None:
            sys.exit("nao ha backfill anterior; rode sem --delta")
        desde = linha[0]
        print(f"modo delta: registros alterados desde {desde} (menos 5 s de margem)")

    ultimo, migradas, quarentena, lidas = "", 0, 0, 0
    t0 = time.time()
    while True:
        consulta = "SELECT cod_ent, st, dt_prev, vlr, transp FROM entrega_tb WHERE cod_ent > %s "
        params = [ultimo]
        if desde:
            consulta += "AND dt_alt >= %s::timestamptz - interval '5 seconds' "
            params.append(desde)
        lote = cl.execute(consulta + "ORDER BY cod_ent LIMIT %s", params + [TAMANHO_LOTE]).fetchall()
        if not lote:
            break
        validas, rejeitadas = [], []
        for cod, st, dt, vlr, transp in lote:
            try:
                e = traducao.do_legado(cod, st, dt, vlr, transp)
                validas.append((e["id"], e["status"], e["previsao"], e["valor_centavos"], e["transportadora_id"], "backfill"))
            except traducao.ErroDeTraducao as erro:
                rejeitadas.append((cod, str(erro), json.dumps({"st": st, "dt_prev": dt, "vlr": vlr, "transp": transp})))
        with cn.transaction():
            cn.cursor().executemany(comum.UPSERT_NOVO, validas)
            cn.cursor().executemany(comum.UPSERT_QUARENTENA, rejeitadas)
        ultimo = lote[-1][0]
        migradas += len(validas)
        quarentena += len(rejeitadas)
        lidas += len(lote)
        print(f"  lote ate {ultimo}: {lidas} lidas, {migradas} migradas, {quarentena} em quarentena", flush=True)

    cn.execute("INSERT INTO controle (chave, valor) VALUES ('backfill_inicio', %s) ON CONFLICT (chave) DO UPDATE SET valor = EXCLUDED.valor",
               (inicio_agora.isoformat(),))
    cn.commit()
    print(f"\nbackfill {'delta ' if delta else ''}concluido em {time.time() - t0:.1f} s: {lidas} lidas, {migradas} migradas, {quarentena} em quarentena")
