"""Worker: consome a fila no ritmo que o banco suporta, com ack, retry com atraso e DLQ.

Topologia (RabbitMQ):
  confirmacoes         fila principal
  confirmacoes.retry   mensagens que falharam esperam aqui 2 s (TTL) e voltam para a fila principal
  confirmacoes.dlq     mensagens que falharam 3 vezes: fila de "cartas mortas", para análise humana

Uma mensagem só sai da fila principal quando o worker dá o ACK, depois de gravar. Se o worker morrer
no meio, o RabbitMQ a entrega de novo (por isso a gravação é idempotente: ON CONFLICT DO NOTHING).
"""
import asyncio
import os
import signal

import aio_pika
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://luna:luna@postgres:5432/confirmacoes")
AMQP_URL = os.environ.get("AMQP_URL", "amqp://guest:guest@rabbitmq/")
PREFETCH = int(os.environ.get("PREFETCH", "8"))
POOL_MAX = int(os.environ.get("POOL_MAX", "8"))
MAX_TENTATIVAS = 3
ATRASO_RETRY_MS = 2000

SQL_GRAVAR = (
    "INSERT INTO confirmacoes (codigo, recebida_em, processada_em) VALUES (%s, now(), now()) "
    "ON CONFLICT (codigo) DO NOTHING"
)


async def main() -> None:
    pool = AsyncConnectionPool(DATABASE_URL, min_size=1, max_size=POOL_MAX, open=False)
    await pool.open()

    conexao = await aio_pika.connect_robust(AMQP_URL)
    canal = await conexao.channel()
    await canal.set_qos(prefetch_count=PREFETCH)             # no máximo PREFETCH mensagens em andamento
    principal = await canal.declare_queue("confirmacoes", durable=True)
    await canal.declare_queue(
        "confirmacoes.retry", durable=True,
        arguments={"x-message-ttl": ATRASO_RETRY_MS, "x-dead-letter-exchange": "",
                   "x-dead-letter-routing-key": "confirmacoes"},
    )
    await canal.declare_queue("confirmacoes.dlq", durable=True)

    async def tratar(mensagem: aio_pika.IncomingMessage) -> None:
        codigo = mensagem.body.decode()
        tentativas = int((mensagem.headers or {}).get("tentativas", 0))
        try:
            if codigo.startswith("VENENO"):                   # mensagem que nunca vai funcionar
                raise ValueError("mensagem invalida")
            async with pool.connection() as conn:
                await conn.execute("SELECT pg_sleep(0.02)")   # custo de trabalho do banco
                await conn.execute(SQL_GRAVAR, (codigo,))
            await mensagem.ack()
        except Exception as erro:
            tentativas += 1
            destino = "confirmacoes.retry" if tentativas < MAX_TENTATIVAS else "confirmacoes.dlq"
            copia = aio_pika.Message(body=mensagem.body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                                     headers={"tentativas": tentativas, "erro": str(erro)})
            await canal.default_exchange.publish(copia, routing_key=destino)
            await mensagem.ack()                              # a original sai; a cópia segue para retry ou DLQ
            print(f"falha em {codigo} (tentativa {tentativas}): vai para {destino}", flush=True)

    await principal.consume(tratar)
    print(f"worker pronto (prefetch={PREFETCH}, pool={POOL_MAX})", flush=True)

    parar = asyncio.Event()
    for sinal in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_running_loop().add_signal_handler(sinal, parar.set)
    await parar.wait()
    await conexao.close()
    await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
