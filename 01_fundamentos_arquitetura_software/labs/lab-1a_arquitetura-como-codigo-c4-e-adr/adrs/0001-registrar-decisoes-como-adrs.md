---
status: accepted
date: 2026-01-12
decision-makers: Roberto, Ana
---
# 0001. Registrar decisões de arquitetura como ADRs no repositório

## Contexto e problema

Decisões importantes são tomadas em conversas, reuniões e cafés, e se perdem. Quem entra no time meses depois não sabe por que o sistema é como é, e as mesmas discussões se repetem.

## Decisão

Cada decisão de arquitetura relevante é registrada em um arquivo Markdown curto (um ADR) na pasta `adrs/` do repositório, no formato MADR. O ADR entra por pull request, junto com a mudança que ele justifica. Um ADR aceito nunca é editado: se a decisão mudar, escreve-se um novo ADR que o substitui.

## Consequências

* Bom, porque o histórico das decisões fica versionado e é revisado como código.
* Bom, porque o ADR e o diagrama mudam no mesmo pull request.
* Ruim, porque exige disciplina: um ADR desatualizado engana mais do que a falta dele.
