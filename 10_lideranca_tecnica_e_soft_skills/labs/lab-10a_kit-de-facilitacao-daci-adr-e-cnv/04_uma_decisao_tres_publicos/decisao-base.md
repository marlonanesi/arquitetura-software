# A decisão (uma fonte, três narrativas)

**Decisão:** migrar o módulo de billing da LunaLog para um SaaS de cobrança, em vez de continuar mantendo-o internamente.

## Os fatos (iguais para todos os públicos)

| Fato | Valor |
|---|---|
| Custo mensal de manter o billing internamente (pessoas e infraestrutura) | R$ 42.000 |
| Custo mensal do SaaS | R$ 26.000 |
| Economia mensal | R$ 16.000 |
| Custo único de integração e migração | R$ 150.000 |
| Prazo de integração | 3 meses |
| Retorno do investimento (integração ÷ economia mensal) | 9,4 meses |
| Pessoas que dominam o billing hoje | 1 |

## O que muda de público para público

**Não mudam os fatos. Muda o que cada pessoa precisa para decidir:**

| Público | A pergunta dele | O que ele precisa ouvir | O que atrapalha |
|---|---|---|---|
| Tech lead | "Vai funcionar tecnicamente e dá para voltar atrás?" | integração, lock-in, reversibilidade, o plano de migração | falar só de custo |
| CFO | "Quanto custa, quando se paga e qual o risco do número?" | custo atual, custo novo, retorno, as premissas | jargão técnico |
| Board | "O que isso protege ou ameaça no negócio?" | o risco de negócio de manter, e o de mudar; a decisão pedida | detalhes, números demais |

## Regras de ouro

1. **Os números são os mesmos** em todos os documentos. Se um número difere, uma das narrativas está errada.
2. **Cada documento começa pela decisão pedida**, não pelo contexto.
3. **Vocabulário do público**: o CFO e o board não precisam de "idempotência" nem de "webhook".
4. **O que cada público vai perguntar** está no documento, com a resposta.
