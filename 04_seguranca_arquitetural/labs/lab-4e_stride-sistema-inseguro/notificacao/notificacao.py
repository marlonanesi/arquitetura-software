"""Serviço de notificação: avisa o destinatário de cada entrega concluída.

O código é o mesmo nas duas versões do sistema. A diferença está na CREDENCIAL de banco que ele recebe
(DATABASE_URL): no sistema inseguro é o administrador do banco; no redesenhado, um papel que só enxerga
id, código e status das entregas e só escreve em "notificacoes".
"""
import os
import time

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]

while True:
    try:
        with psycopg.connect(DATABASE_URL, autocommit=True) as c:
            pendentes = c.execute(
                "SELECT id, codigo FROM entregas WHERE status = 'entregue' "
                "AND id NOT IN (SELECT entrega_id FROM notificacoes)").fetchall()
            for entrega_id, codigo in pendentes:
                c.execute("INSERT INTO notificacoes (entrega_id) VALUES (%s)", (entrega_id,))
                print(f"notificacao enviada: entrega {codigo}", flush=True)
    except psycopg.Error as erro:
        print(f"erro: {erro}", flush=True)
    time.sleep(2)
