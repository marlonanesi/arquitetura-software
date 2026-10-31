---
status: accepted
date: 2026-08-17
decision-makers: Roberto, Ana
---
# 0005. PostgreSQL com JSONB para o módulo de rastreamento

## Contexto e problema

Seis meses depois, o esquema do rastreamento se estabilizou, o time opera dois bancos e os relatórios precisam cruzar entregas com cobrança. Um novo desenvolvedor perdeu dois dias descobrindo por que o rastreamento usava um banco diferente (veja o ADR 0003).

## Decisão

Migrar o estado das entregas para o PostgreSQL, guardando o payload variável de cada transportadora em colunas JSONB. Este ADR substitui o [0003](0003-mongodb-para-o-rastreamento.md).

## Consequências

* Bom, porque há uma única tecnologia de banco, e os relatórios cruzam os dados com SQL.
* Bom, porque o JSONB mantém a flexibilidade para os payloads variáveis.
* Ruim, porque exige uma migração de dados (veja a trilha de migração do curso).
