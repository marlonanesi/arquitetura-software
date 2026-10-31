"""Reconstrói as projeções DO ZERO a partir dos eventos (replay) e prova que o resultado é idêntico.

  python reconstruir.py            reconstrói e compara com o que havia
  python reconstruir.py --novo     reconstrói e mostra o que mudou (use depois de alterar o código de uma projeção)

Como as projeções são derivadas, elas são descartáveis: quando o formato de uma consulta muda, não há migração
de dados, só um replay. Para este script, o projetor deve estar parado (ele disputaria as mesmas tabelas).
"""
import json
import sys
import time

import psycopg

import projecoes
from store import DATABASE_URL

with psycopg.connect(DATABASE_URL, autocommit=True) as c:
    antes = projecoes.impressao_digital(c)
    total = c.execute("SELECT count(*) FROM eventos").fetchone()[0]
    inicio = time.time()
    with c.transaction():
        c.execute("TRUNCATE proj_entregas, proj_painel")
        for agregado, versao, tipo, esquema, dados in c.execute("SELECT agregado_id, versao, tipo, esquema, dados FROM eventos ORDER BY id").fetchall():
            projecoes.aplicar_evento(c, agregado, versao, tipo, esquema, dados if isinstance(dados, dict) else json.loads(dados))
        ultimo = c.execute("SELECT coalesce(max(id), 0) FROM eventos").fetchone()[0]
        c.execute("UPDATE projetor_controle SET valor = %s WHERE nome = 'ultimo_evento'", (ultimo,))
    depois = projecoes.impressao_digital(c)

print(f"replay de {total} eventos em {time.time() - inicio:.2f} s")
print(f"impressao digital das projecoes: antes={antes} depois={depois}  ->  {'IDENTICA' if antes == depois else 'DIFERENTE'}")
