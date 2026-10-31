---
status: superseded by ADR-0005
date: 2026-02-02
decision-makers: Roberto
---
# 0003. MongoDB para o módulo de rastreamento

## Contexto e problema

Os eventos de rastreamento têm formatos variados por transportadora, e o esquema parecia instável.

## Decisão

Usar o MongoDB para o estado e o histórico das entregas.

## Consequências

* Bom, porque aceita documentos de formatos diferentes sem migração.
* Ruim, porque o restante do sistema usa PostgreSQL: duas tecnologias de banco para operar e consultas entre elas só pela aplicação.
