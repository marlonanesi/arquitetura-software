---
status: accepted
date: 2026-02-09
decision-makers: Roberto, Ana, Camila (segurança)
---
# 0004. API Gateway na borda para autenticação e limite de taxa

## Contexto e problema

Cada serviço implementava autenticação e limite de taxa do seu jeito, com inconsistências e brechas.

## Decisão

Um API Gateway na borda concentra autenticação, limite de taxa e roteamento. Os serviços internos confiam na identidade validada pelo gateway.

## Consequências

* Bom, porque a política de segurança de borda fica em um só lugar.
* Ruim, porque o gateway é um ponto único de falha e precisa ser replicado.
