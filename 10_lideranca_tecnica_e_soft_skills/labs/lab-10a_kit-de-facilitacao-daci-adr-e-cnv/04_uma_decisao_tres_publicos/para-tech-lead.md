# Billing em SaaS: a proposta para o tech lead

**Decisão pedida:** aprovar a migração do billing para um SaaS de cobrança, em três meses, com migração gradual.

## O problema técnico

O módulo de billing é o mais acoplado da LunaLog: qualquer mudança nele quebra algo em outro módulo (o diagnóstico da aula 8.1). Só **uma pessoa** domina a lógica de cobrança, as regras fiscais mudam com frequência, e o custo de manter isso internamente é de **R$ 42.000** por mês.

## A proposta

Substituir o módulo por um SaaS de cobrança, com **R$ 26.000** por mês, e um custo único de integração de **R$ 150.000**. A integração leva **3 meses**, e o investimento se paga em **9,4 meses** depois de a economia começar.

## Os trade-offs técnicos

| Aspecto | Hoje (interno) | Com o SaaS |
|---|---|---|
| Complexidade de integração | nenhuma, mas o acoplamento é nosso | uma camada de integração (eventos de cobrança, conciliação) |
| **Lock-in** | nenhum | alto: o modelo de dados e as regras passam a ser do fornecedor |
| Regras fiscais | nossas, com 1 pessoa | do fornecedor, com atualização contratual |
| Disponibilidade | a nossa | a do fornecedor (SLA contratual) |
| **Reversibilidade** | n/a | média, se mantivermos o modelo de dados canônico fora do SaaS |

## Como reduzimos o risco

1. **Anti-corruption layer** entre a LunaLog e o SaaS (lab 8C): o nosso modelo não passa a falar o idioma do fornecedor.
2. **Migração gradual** (strangler, lab 8B), por tipo de cobrança, com dual-write e reconciliação (lab 8D), e rollback em cada etapa.
3. **Dados canônicos** guardados por nós: o histórico de cobranças continua nosso, para a saída ser possível.
4. **Cláusulas de saída** no contrato: exportação completa dos dados e prazo de transição.

## O que vão perguntar

- *"E se o fornecedor mudar o preço ou sair do mercado?"* A camada de integração e o modelo canônico mantêm a troca possível; o custo de saída é estimado em uma fração do da integração.
- *"Por que não refatorar o módulo?"* O custo de refatorar não resolve a dependência de uma pessoa nem as regras fiscais, que são o que muda mais.
