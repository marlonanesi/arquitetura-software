"""Os dados da migração (síntese dos passos do lab 8D, no mesmo estilo):

  python dados.py backfill      copia o histórico do legado para o novo (em lotes, idempotente)
  python dados.py verificar     compara os dois bancos (contagem e conteúdo, já traduzido); sai com 1 se divergir
  python dados.py reconciliar   repara o novo a partir do legado (a verdade até a virada da escrita)
  python dados.py reconciliar-legado   depois da virada: repara a CÓPIA do legado a partir do novo (a verdade agora)
"""
import sys

import psycopg

sys.path.insert(0, "/app")
import traducao  # noqa: E402

URL_LEGADO = "postgresql://luna:luna@postgres:5432/legado"
URL_NOVO = "postgresql://luna:luna@postgres:5432/novo"
UPSERT = ("INSERT INTO entregas (id, status, previsao, valor_centavos, transportadora_id, origem) VALUES (%s, %s, %s, %s, %s, %s) "
          "ON CONFLICT (id) DO UPDATE SET status = EXCLUDED.status, previsao = EXCLUDED.previsao, valor_centavos = EXCLUDED.valor_centavos, "
          "transportadora_id = EXCLUDED.transportadora_id, origem = EXCLUDED.origem, atualizado_em = now() "
          "WHERE entregas.origem <> 'novo-primario'")


def ler_legado(c):
    return {cod: traducao.do_legado(cod, st, dt, vlr, tr) for cod, st, dt, vlr, tr in
            c.execute("SELECT cod_ent, st, dt_prev, vlr, transp FROM entrega_tb")}


def ler_novo(c):
    return {i: {"id": i, "status": s, "previsao": p, "valor_centavos": v, "transportadora_id": t} for i, s, p, v, t in
            c.execute("SELECT id, status, previsao, valor_centavos, transportadora_id FROM entregas")}


def linhas(entregas, origem):
    return [(e["id"], e["status"], e["previsao"], e["valor_centavos"], e["transportadora_id"], origem) for e in entregas]


def divergencias(legado, novo):
    faltando = [i for i in legado if i not in novo]
    diferentes = [i for i in legado if i in novo and traducao.forma_canonica(legado[i]) != traducao.forma_canonica(novo[i])]
    return faltando, diferentes


comando = sys.argv[1] if len(sys.argv) > 1 else "verificar"
with psycopg.connect(URL_LEGADO) as cl, psycopg.connect(URL_NOVO, autocommit=True) as cn:
    legado, novo = ler_legado(cl), ler_novo(cn)
    if comando == "backfill":
        with cn.transaction():
            cn.cursor().executemany(UPSERT, linhas(legado.values(), "backfill"))
        print(f"backfill: {len(legado)} entregas copiadas para o banco novo")
    elif comando == "reconciliar":
        faltando, diferentes = divergencias(legado, novo)
        with cn.transaction():
            cn.cursor().executemany(UPSERT, linhas((legado[i] for i in faltando + diferentes), "reconciliacao"))
        cl.execute("DELETE FROM fila_reparo")
        cl.commit()
        print(f"reconciliacao: {len(faltando)} faltando e {len(diferentes)} diferentes reparados; fila de reparo esvaziada")
    elif comando == "reconciliar-legado":
        faltando, diferentes = divergencias(legado, novo)
        with cl.transaction():
            for i in faltando + diferentes:
                cl.execute("INSERT INTO entrega_tb (cod_ent, st, dt_prev, vlr, transp, dt_alt) VALUES (%s, %s, %s, %s, %s, now()) "
                           "ON CONFLICT (cod_ent) DO UPDATE SET st = EXCLUDED.st, dt_prev = EXCLUDED.dt_prev, vlr = EXCLUDED.vlr, transp = EXCLUDED.transp, dt_alt = now()",
                           traducao.para_legado(novo[i]))
        print(f"reconciliacao (novo -> legado): {len(faltando)} faltando e {len(diferentes)} diferentes reparados na copia do legado")
    else:
        faltando, diferentes = divergencias(legado, novo)
        print(f"legado: {len(legado)} entregas | novo: {len(novo)} | faltando no novo: {len(faltando)} | diferentes: {len(diferentes)}")
        print("RESULTADO: " + ("CONSISTENTE" if not (faltando or diferentes) else "DIVERGENTE"))
        sys.exit(0 if not (faltando or diferentes) else 1)
