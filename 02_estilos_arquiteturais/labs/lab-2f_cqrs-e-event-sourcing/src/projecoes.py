"""As projeções (modelos de LEITURA) e o código que as atualiza a partir dos eventos.

Duas projeções, para duas perguntas diferentes, cada uma no formato que a consulta pede:
  proj_entregas  o estado atual de cada entrega (consulta por id)
  proj_painel    totais por transportadora (consulta do painel)
O mesmo fluxo de eventos alimenta as duas, e qualquer uma pode ser descartada e reconstruída.
"""
import hashlib
import json

import psycopg

from dominio import atualizar_esquema


def aplicar_evento(c: psycopg.Connection, agregado_id: str, versao: int, tipo: str, esquema: int, dados: dict) -> None:
    e = atualizar_esquema({"tipo": tipo, "esquema": esquema, "dados": dados})
    d = e["dados"]
    if tipo == "EntregaRegistrada":
        c.execute("INSERT INTO proj_entregas (id, codigo, status, previsao, transportadora, versao) VALUES (%s, %s, 'criada', %s, %s, %s) "
                  "ON CONFLICT (id) DO NOTHING", (agregado_id, d["codigo"], d["previsao"], d["transportadora"], versao))
        c.execute("INSERT INTO proj_painel (transportadora, registradas) VALUES (%s, 1) "
                  "ON CONFLICT (transportadora) DO UPDATE SET registradas = proj_painel.registradas + 1", (d["transportadora"],))
        return

    status_anterior, transportadora = c.execute("SELECT status, transportadora FROM proj_entregas WHERE id = %s", (agregado_id,)).fetchone()
    if tipo == "RotaIniciada":
        c.execute("UPDATE proj_entregas SET status = 'em_rota', versao = %s, atualizado_em = now() WHERE id = %s", (versao, agregado_id))
        c.execute("UPDATE proj_painel SET em_rota = em_rota + 1 WHERE transportadora = %s", (transportadora,))
    elif tipo == "EntregaReagendada":
        c.execute("UPDATE proj_entregas SET previsao = %s, reagendamentos = reagendamentos + 1, versao = %s, atualizado_em = now() WHERE id = %s",
                  (d["nova_previsao"], versao, agregado_id))
        c.execute("UPDATE proj_painel SET reagendamentos = reagendamentos + 1 WHERE transportadora = %s", (transportadora,))
    elif tipo == "EntregaConfirmada":
        c.execute("UPDATE proj_entregas SET status = 'entregue', versao = %s, atualizado_em = now() WHERE id = %s", (versao, agregado_id))
        c.execute("UPDATE proj_painel SET em_rota = em_rota - 1, entregues = entregues + 1 WHERE transportadora = %s", (transportadora,))
    elif tipo == "EntregaCancelada":
        c.execute("UPDATE proj_entregas SET status = 'cancelada', versao = %s, atualizado_em = now() WHERE id = %s", (versao, agregado_id))
        c.execute("UPDATE proj_painel SET canceladas = canceladas + 1, em_rota = em_rota - %s WHERE transportadora = %s",
                  (1 if status_anterior == "em_rota" else 0, transportadora))


def impressao_digital(c: psycopg.Connection) -> str:
    """Resumo estável do conteúdo das projeções (ignora campos de horário), para comparar antes e depois."""
    h = hashlib.sha256()
    for linha in c.execute("SELECT id, codigo, status, previsao, transportadora, reagendamentos, versao FROM proj_entregas ORDER BY id"):
        h.update(json.dumps(linha).encode())
    for linha in c.execute("SELECT * FROM proj_painel ORDER BY transportadora"):
        h.update(json.dumps(linha).encode())
    return h.hexdigest()[:16]
