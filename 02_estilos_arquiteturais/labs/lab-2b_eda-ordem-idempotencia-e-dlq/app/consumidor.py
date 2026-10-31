"""Consumer de eventos de entrega da LunaLog, em dois modos.

MODO=ingenuo : processa tudo na ordem em que chega, sem proteção nenhuma.
MODO=robusto : idempotente, ignora evento antigo, tenta de novo e manda para a DLQ.

PAPEL=estado       : atualiza o estado da entrega e a comissão do motorista.
PAPEL=notificacao  : registra a notificação enviada ao cliente (só no modo robusto).
"""
import json
import os
import signal
import time
from datetime import datetime

import psycopg
from confluent_kafka import Consumer, Producer

MODO = os.environ["MODO"]
GRUPO = os.environ["GRUPO"]
PAPEL = os.environ.get("PAPEL", "estado")
BROKERS = os.environ["BROKERS"]
DATABASE_URL = os.environ["DATABASE_URL"]
SUPORTA_DEVOLVIDA = os.environ.get("SUPORTA_DEVOLVIDA", "0") == "1"

TOPICO = "entregas.eventos"
TOPICO_DLQ = "entregas.eventos.dlq"
MAX_TENTATIVAS = 3
COMISSAO_POR_ENTREGA = 12  # R$ creditados ao motorista quando a entrega é concluída

TIPOS_CONHECIDOS = {"criada", "coletada", "em_rota", "entregue"}
if SUPORTA_DEVOLVIDA:
    TIPOS_CONHECIDOS.add("devolvida")


def log(msg):
    print(f"{datetime.now():%H:%M:%S} [{GRUPO}] {msg}", flush=True)


def corr_id(msg):
    for chave, valor in msg.headers() or []:
        if chave == "correlation_id":
            return valor.decode()
    return "-"


# --------------------------------------------------------------------------- ingênuo
def processar_ingenuo(conn, evento):
    # Sem validar nada: um tipo novo derruba o processo com KeyError.
    status = {"criada": "criada", "coletada": "coletada", "em_rota": "em_rota", "entregue": "entregue"}[evento["tipo"]]
    with conn.transaction():
        conn.execute(
            """INSERT INTO ingenuo_entregas (entrega_id, status) VALUES (%s, %s)
               ON CONFLICT (entrega_id) DO UPDATE SET status = EXCLUDED.status""",
            (evento["entrega_id"], status),
        )
        if evento["tipo"] == "entregue":
            conn.execute(
                "UPDATE ingenuo_entregas SET comissao_motorista = comissao_motorista + %s WHERE entrega_id = %s",
                (COMISSAO_POR_ENTREGA, evento["entrega_id"]),
            )
    return "aplicado"


# --------------------------------------------------------------------------- robusto
def validar(evento):
    for campo in ("event_id", "entrega_id", "tipo", "seq"):
        if campo not in evento:
            raise ValueError(f"campo obrigatório ausente: {campo}")
    if evento["tipo"] not in TIPOS_CONHECIDOS:
        raise ValueError(f"tipo de evento desconhecido: {evento['tipo']}")


def processar_robusto(conn, evento, corr):
    validar(evento)
    with conn.transaction():
        # 1) Idempotência: a marca de "já processado" e o efeito andam na MESMA transação.
        cur = conn.execute(
            "INSERT INTO eventos_processados (grupo, event_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (GRUPO, evento["event_id"]),
        )
        if cur.rowcount == 0:
            return "duplicado ignorado"

        if PAPEL == "notificacao":
            conn.execute(
                "INSERT INTO notificacoes (event_id, entrega_id, mensagem, correlation_id) VALUES (%s, %s, %s, %s)",
                (evento["event_id"], evento["entrega_id"],
                 f"Sua entrega {evento['entrega_id']} agora esta: {evento['tipo']}", corr),
            )
            return "notificacao registrada"

        # 2) Ordem: só aplica se o evento é mais novo que o estado atual (versão "seq").
        aplicado = conn.execute(
            """INSERT INTO robusto_entregas (entrega_id, status, seq) VALUES (%s, %s, %s)
               ON CONFLICT (entrega_id) DO UPDATE SET status = EXCLUDED.status, seq = EXCLUDED.seq
               WHERE robusto_entregas.seq < EXCLUDED.seq
               RETURNING 1""",
            (evento["entrega_id"], evento["tipo"], evento["seq"]),
        ).fetchone()
        if aplicado is None:
            return f"evento antigo ignorado (seq {evento['seq']} <= estado atual)"
        if evento["tipo"] == "entregue":
            conn.execute(
                "UPDATE robusto_entregas SET comissao_motorista = comissao_motorista + %s WHERE entrega_id = %s",
                (COMISSAO_POR_ENTREGA, evento["entrega_id"]),
            )
        return "aplicado"


def enviar_para_dlq(produtor, msg, erro, tentativas):
    cabecalhos = list(msg.headers() or []) + [
        ("dlq.erro", str(erro).encode()),
        ("dlq.tentativas", str(tentativas).encode()),
        ("dlq.origem", f"{msg.topic()}[{msg.partition()}]@{msg.offset()}".encode()),
        ("dlq.grupo", GRUPO.encode()),
    ]
    produtor.produce(TOPICO_DLQ, key=msg.key(), value=msg.value(), headers=cabecalhos)
    produtor.flush()


def main():
    consumer = Consumer({
        "bootstrap.servers": BROKERS,
        "group.id": GRUPO,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,  # o offset só avança depois de processar
        "session.timeout.ms": 10000,
    })
    produtor_dlq = Producer({"bootstrap.servers": BROKERS})
    consumer.subscribe([TOPICO])
    log(f"iniciado: modo={MODO} papel={PAPEL} suporta_devolvida={SUPORTA_DEVOLVIDA}")

    # Saída limpa: ao receber SIGTERM o consumer deixa o grupo na hora, sem esperar o timeout de sessão.
    encerrar = {"sim": False}
    for sinal in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sinal, lambda *_: encerrar.update(sim=True))

    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        while not encerrar["sim"]:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                log(f"erro do broker: {msg.error()}")
                continue

            corr = corr_id(msg)
            origem = f"p{msg.partition()}@{msg.offset()}"

            if MODO == "ingenuo":
                evento = json.loads(msg.value())  # sem try/except: se falhar, o processo cai
                resultado = processar_ingenuo(conn, evento)
                log(f"{origem} corr={corr} {evento['entrega_id']} {evento['tipo']} -> {resultado}")
                consumer.commit(msg)
                continue

            # modo robusto: tenta algumas vezes e, se não der, isola a mensagem na DLQ
            ultimo_erro = None
            for tentativa in range(1, MAX_TENTATIVAS + 1):
                try:
                    evento = json.loads(msg.value())
                    resultado = processar_robusto(conn, evento, corr)
                    log(f"{origem} corr={corr} {evento['entrega_id']} {evento['tipo']} seq={evento['seq']} -> {resultado}")
                    break
                except Exception as erro:  # noqa: BLE001 - qualquer falha deve acabar na DLQ
                    ultimo_erro = erro
                    log(f"{origem} corr={corr} tentativa {tentativa}/{MAX_TENTATIVAS} falhou: {erro}")
                    time.sleep(0.5 * tentativa)
            else:
                enviar_para_dlq(produtor_dlq, msg, ultimo_erro, MAX_TENTATIVAS)
                log(f"{origem} corr={corr} enviada para a DLQ ({TOPICO_DLQ})")
            consumer.commit(msg)

    consumer.close()
    log("encerrado")


if __name__ == "__main__":
    main()
