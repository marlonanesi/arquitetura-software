---
status: accepted
date: 2026-01-19
decision-makers: Roberto, Ana
---
# 0002. Kafka como barramento de eventos entre os serviços

## Contexto e problema

O rastreamento precisa avisar a notificação, a roteirização e, no futuro, a analítica, sempre que uma entrega muda de estado. Chamadas síncronas entre serviços criam acoplamento temporal e uma cadeia de falhas.

## Alternativas consideradas

* Chamadas HTTP diretas entre os serviços
* RabbitMQ (fila clássica)
* Kafka (log de eventos)

## Decisão

Usar o Kafka como barramento de eventos. A retenção do log permite reprocessar eventos e adicionar consumidores novos sem mexer no produtor.

## Consequências

* Bom, porque o produtor não conhece os consumidores.
* Bom, porque o histórico de eventos pode ser reexecutado.
* Ruim, porque aumenta a complexidade operacional e exige cuidado com ordenação por chave e com idempotência no consumidor.
