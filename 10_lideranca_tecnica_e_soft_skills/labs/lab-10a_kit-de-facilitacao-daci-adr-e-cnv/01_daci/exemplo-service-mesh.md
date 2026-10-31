# DACI: qual service mesh a LunaLog adota?

**Decisão:** adotamos o Istio ou o Linkerd como service mesh dos serviços da LunaLog?
**Decisão até:** 2026-11-13
**Contexto:** o requisito de mTLS entre serviços (cliente farmacêutico) vence no próximo trimestre. Sem decisão, cada time implementa o seu próprio TLS, e voltamos ao problema das doze autorizações diferentes.

## Papéis

| Papel | Pessoa | O que faz |
|---|---|---|
| D (Driver) | Ana | conduz a sessão, reúne os dados da prova de conceito, garante a decisão no prazo |
| A (Approver) | Roberto | decide, depois de ouvir, e responde pela decisão |
| C (Contributor) | Camila (segurança) | avalia o modelo de identidade e de políticas |
| C (Contributor) | Diego (plataforma) | estima o custo operacional de cada opção |
| C (Contributor) | Eva (time de rastreamento) | avalia o impacto nos serviços que mais recebem tráfego |
| I (Informed) | Times de produto | avisados do prazo de migração |
| I (Informed) | Cliente farmacêutico (via comercial) | informado do cronograma de mTLS |

## Opções

| Opção | Resumo | A favor | Contra |
|---|---|---|---|
| Istio | malha completa, com políticas de autorização, gateways e telemetria | mais recursos, comunidade maior, o lab 4F já o usa | mais complexo de operar; mais consumo de recursos |
| Linkerd | malha enxuta, foco em mTLS e observabilidade básica | simples de operar, leve | menos recursos; autorização por política mais limitada |

## Critérios (combinados antes de discutir as opções)

1. Atende o requisito de mTLS com identidade por serviço e prazo de certificado curto.
2. Custo de operar: quantas pessoas-hora por mês e quanta memória por pod.
3. Capacidade de autorização por identidade (quem pode chamar quem).
4. Reversibilidade: quanto custa desistir depois.

## Resultado

**Decisão tomada:** Istio, em modo estrito de mTLS e com autorização por identidade, começando por um namespace.
**Registrada em:** ADR 0008 (`02_sessao_de_decisao/adr-resultado-exemplo.md`).
