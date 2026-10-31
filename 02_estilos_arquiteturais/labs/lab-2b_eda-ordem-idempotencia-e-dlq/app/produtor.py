"""Produtor de cenários do lab 2B.

Uso: python produtor.py <cenario>

Cenários: feliz, duplicado, fora-de-ordem, evento-novo, particoes, reprocessar-dlq
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone

from confluent_kafka import Consumer, Producer

BROKERS = os.environ["BROKERS"]
TOPICO = "entregas.eventos"
TOPICO_DLQ = "entregas.eventos.dlq"
TOPICO_DEMO = "demo.particoes"

SEQ = {"criada": 1, "coletada": 2, "em_rota": 3, "entregue": 4, "devolvida": 4}

produtor = Producer({"bootstrap.servers": BROKERS})
# Sem chave, o particionador padrão "gruda" lotes em uma partição só; para a demonstração
# queremos ver a distribuição entre partições, como acontece com muitos produtores em paralelo.
# Por isso o cenário "particoes" publica as mensagens sem chave em lote (um flush só no fim):
# um flush por mensagem faria cada uma sair sozinha e cair na mesma partição.
produtor_sem_chave = Producer({"bootstrap.servers": BROKERS, "partitioner": "random"})


def evento(entrega, tipo, seq=None):
    seq = SEQ[tipo] if seq is None else seq
    return {
        "event_id": f"{entrega}-{seq}-{tipo}",  # identidade do fato: se repetir, é duplicado
        "entrega_id": entrega,
        "tipo": tipo,
        "seq": seq,
        "ocorrido_em": datetime.now(timezone.utc).isoformat(),
    }


def publicar(ev, corr, topico=TOPICO, chave=True, mostrar=True, flush=True):
    def ao_entregar(err, msg):
        if err:
            print(f"  falha ao publicar: {err}")
        elif mostrar:
            print(f"  {ev['entrega_id']} {ev['tipo']:<9} seq={ev['seq']} -> particao {msg.partition()}, offset {msg.offset()}")

    p = produtor if chave else produtor_sem_chave
    p.produce(
        topico,
        key=ev["entrega_id"] if chave else None,
        value=json.dumps(ev).encode(),
        headers=[("correlation_id", corr.encode())],
        on_delivery=ao_entregar,
    )
    if flush:
        p.flush()


def corr_para(entrega):
    return f"corr-{entrega}-{uuid.uuid4().hex[:6]}"


def cenario_feliz():
    print("Cenario feliz: 4 entregas, 4 eventos cada, tudo em ordem e com chave = entrega_id")
    for n in range(1, 5):
        entrega = f"E-00{n}"
        corr = corr_para(entrega)
        for tipo in ("criada", "coletada", "em_rota", "entregue"):
            publicar(evento(entrega, tipo), corr)


def cenario_duplicado():
    print("Cenario duplicado: o broker entrega 'entregue' da E-100 duas vezes (at-least-once)")
    entrega = "E-100"
    corr = corr_para(entrega)
    for tipo in ("criada", "coletada", "em_rota", "entregue"):
        publicar(evento(entrega, tipo), corr)
    print("  ... redelivery do mesmo evento (mesmo event_id):")
    publicar(evento(entrega, "entregue"), corr)


def cenario_fora_de_ordem():
    print("Cenario fora de ordem: 'entregue' (seq 4) chega ANTES de 'em_rota' (seq 3) na E-200")
    entrega = "E-200"
    corr = corr_para(entrega)
    for tipo, seq in (("criada", 1), ("coletada", 2), ("entregue", 4), ("em_rota", 3)):
        publicar(evento(entrega, tipo, seq), corr)


def cenario_evento_novo():
    print("Cenario evento novo: o produtor ja publica 'devolvida', que os consumers ainda nao conhecem")
    entrega = "E-300"
    corr = corr_para(entrega)
    for tipo in ("criada", "coletada", "em_rota", "devolvida"):
        publicar(evento(entrega, tipo), corr)
    print("  ... e depois outra entrega totalmente normal, que fica ATRAS da mensagem problematica:")
    entrega = "E-301"
    corr = corr_para(entrega)
    for tipo in ("criada", "coletada", "em_rota", "entregue"):
        publicar(evento(entrega, tipo), corr)


def cenario_particoes():
    print("Cenario particoes: 6 eventos da MESMA entrega, com chave e sem chave (topico demo.particoes)")
    print("Com chave = entrega_id (o broker aplica hash na chave):")
    for tipo in ("criada", "coletada", "em_rota", "entregue", "criada", "coletada"):
        publicar(evento("E-900", tipo, SEQ[tipo]), corr_para("E-900"), topico=TOPICO_DEMO, chave=True)
    print("Sem chave (o broker espalha entre as particoes):")
    for tipo in ("criada", "coletada", "em_rota", "entregue", "criada", "coletada"):
        publicar(evento("E-901", tipo, SEQ[tipo]), corr_para("E-901"), topico=TOPICO_DEMO, chave=False, flush=False)
    produtor_sem_chave.flush()


def cenario_reprocessar_dlq():
    print("Reprocessando a DLQ: lendo mensagens isoladas e republicando no topico principal")
    consumer = Consumer({
        "bootstrap.servers": BROKERS,
        "group.id": f"reprocessador-{uuid.uuid4().hex[:6]}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })
    consumer.subscribe([TOPICO_DLQ])
    vazios, total = 0, 0
    while vazios < 5:
        msg = consumer.poll(1.0)
        if msg is None or msg.error():
            vazios += 1
            continue
        vazios = 0
        cabecalhos = {k: v.decode() for k, v in (msg.headers() or []) if not k.startswith("dlq.")}
        motivo = next((v.decode() for k, v in (msg.headers() or []) if k == "dlq.erro"), "?")
        produtor.produce(TOPICO, key=msg.key(), value=msg.value(),
                         headers=[(k, v.encode()) for k, v in cabecalhos.items()])
        produtor.flush()
        total += 1
        print(f"  republicada: {json.loads(msg.value())['entrega_id']} (motivo original: {motivo})")
    consumer.close()
    print(f"Total reprocessado: {total}")


CENARIOS = {
    "feliz": cenario_feliz,
    "duplicado": cenario_duplicado,
    "fora-de-ordem": cenario_fora_de_ordem,
    "evento-novo": cenario_evento_novo,
    "particoes": cenario_particoes,
    "reprocessar-dlq": cenario_reprocessar_dlq,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in CENARIOS:
        print(__doc__)
        sys.exit(1)
    CENARIOS[sys.argv[1]]()
