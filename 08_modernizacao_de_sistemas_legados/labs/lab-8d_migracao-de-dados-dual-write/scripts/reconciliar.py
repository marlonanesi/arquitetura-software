"""Reconciliação: encontra as divergências e repara o banco novo a partir do legado (a verdade, até o cutover).

  python reconciliar.py

Estratégia: compara linha a linha, regrava no novo o que falta ou está diferente, e esvazia a fila de reparo
(divergências que o dual-write registrou quando uma escrita no novo falhou). Não toca em registros cuja
origem é 'novo-primario': depois do cutover da escrita, o novo é a verdade.
"""
import comum
import traducao

with comum.legado() as cl, comum.novo() as cn:
    validas, _ = comum.ler_legado_traduzido(cl)
    no_novo = comum.ler_novo(cn)
    fila = cl.execute("SELECT count(*) FROM fila_reparo").fetchone()[0]

    a_reparar = [c for c in validas if c not in no_novo or traducao.forma_canonica(validas[c]) != traducao.forma_canonica(no_novo[c])]
    linhas = [(e["id"], e["status"], e["previsao"], e["valor_centavos"], e["transportadora_id"], "reconciliacao")
              for e in (validas[c] for c in a_reparar)]
    with cn.transaction():
        cn.cursor().executemany(comum.UPSERT_NOVO, linhas)
    cl.execute("DELETE FROM fila_reparo")
    cl.commit()
    print(f"reconciliacao: {len(a_reparar)} registros reparados no novo; fila de reparo tinha {fila} itens (agora vazia)")
