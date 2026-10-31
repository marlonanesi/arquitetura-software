"""O projetor: lê os eventos novos do event store e atualiza os modelos de leitura.

Roda em separado da API (por isso a leitura é EVENTUALMENTE consistente). Para mostrar isso, o atraso por evento
pode ser aumentado em tempo de execução (POST /admin/atraso na API grava em projetor_controle.atraso_ms).
"""
import json
import time

import psycopg

import projecoes
from store import DATABASE_URL

print("projetor iniciado", flush=True)
while True:
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as c:
            while True:
                ultimo, atraso = (c.execute("SELECT valor FROM projetor_controle WHERE nome = 'ultimo_evento'").fetchone()[0],
                                  c.execute("SELECT valor FROM projetor_controle WHERE nome = 'atraso_ms'").fetchone()[0])
                lote = c.execute("SELECT id, agregado_id, versao, tipo, esquema, dados FROM eventos WHERE id > %s ORDER BY id LIMIT 50", (ultimo,)).fetchall()
                if not lote:
                    time.sleep(0.2)
                    continue
                for id_, agregado, versao, tipo, esquema, dados in lote:
                    with c.transaction():                      # a projeção e o ponteiro avançam juntos
                        projecoes.aplicar_evento(c, agregado, versao, tipo, esquema, dados if isinstance(dados, dict) else json.loads(dados))
                        c.execute("UPDATE projetor_controle SET valor = %s WHERE nome = 'ultimo_evento'", (id_,))
                    if atraso:
                        time.sleep(atraso / 1000)
    except psycopg.Error as erro:
        print(f"erro no projetor: {erro}; tentando de novo", flush=True)
        time.sleep(1)
