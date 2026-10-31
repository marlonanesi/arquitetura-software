---
status: proposed
date: 2026-10-27
decision-makers: Roberto, Ana
---
# 0007. Cache de consulta do estado da entrega com Redis

## Contexto e problema

O painel consulta o estado das entregas a cada poucos segundos e pressiona o banco.

## Decisão

Proposta: um cache Redis na frente do banco para as consultas de estado, invalidado a cada evento.

## Consequências

* Bom, porque reduz a carga de leitura no banco.
* Ruim, porque introduz invalidação de cache e mais um componente para operar.
