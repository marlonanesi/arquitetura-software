---
status: proposed
date: 2026-10-05
decision-makers: Roberto, Ana
---
# 0006. Event Sourcing no módulo de rastreamento

## Contexto e problema

Disputas com clientes exigem reconstruir o estado de uma entrega em um instante passado. Hoje só guardamos o estado atual e um log parcial.

## Decisão

Proposta: gravar cada mudança como evento imutável e derivar o estado atual a partir deles. Em discussão: o custo de evoluir o esquema dos eventos e a necessidade de projeções para leitura.

## Consequências

* Bom, porque o histórico completo vira a fonte da verdade.
* Ruim, porque aumenta a complexidade e exige modelos de leitura separados. A decisão depende de uma prova de conceito.
