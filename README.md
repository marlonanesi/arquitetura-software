# Arquitetura de Software na Prática

Material de apoio do curso **Arquitetura de Software: Pense e Decida como Arquiteto!**.

Cada seção contém os slides das aulas em formato `.pdf`.

---

## Estrutura do Repositório

```
.
├── 01_fundamentos_arquitetura_software/
├── 02_estilos_arquiteturais/
├── 03_escalabilidade_e_design_de_apis/
├── 04_seguranca_arquitetural/
├── 05_ci_cd_e_estrategias_de_deploy/
├── 06_observabilidade/
├── 07_confiabilidade_e_sre/
├── 08_modernizacao_de_sistemas_legados/
├── 09_arquitetura_evolutiva_e_governanca/
└── 10_lideranca_tecnica_e_soft_skills/
```

---

## Seções

### 01 — Fundamentos e Visão Arquitetural
O que é arquitetura de software, por que ela importa para o negócio e quais ferramentas o arquiteto usa para tomar e documentar decisões estruturais: atributos de qualidade, trade-offs, ADR e C4 Model.

### 02 — Estilos Arquiteturais na Prática
Comparativo entre monólito, microsserviços, serverless, EDA e contêineres com trade-offs reais. Inclui arquitetura hexagonal, CQRS, Event Sourcing e critérios objetivos para escolher o estilo certo para cada contexto.

### 03 — Design de Sistemas Escaláveis
Escalabilidade horizontal e vertical, load balancing, caching distribuído, filas de mensagens, design de APIs REST, gRPC, GraphQL, rate limiting, circuit breaker e estratégias de banco de dados para larga escala.

### 04 — Segurança Arquitetural
Criptografia (simétrica, assimétrica, envelope encryption), TLS/mTLS, OAuth 2.1, OpenID Connect, JWT, MFA, SSO, RBAC/ABAC/ReBAC, policy-as-code, threat modeling com STRIDE e zero trust com service mesh.

### 05 — CI/CD e Estratégias de Deploy
Pipelines maduros com stages e quality gates, consumer-driven contracts com Pact, blue/green, rolling deployment, canary release, feature flags e padrões de rollback com expand-contract.

### 06 — Observabilidade e Monitoramento
Os três pilares: logs estruturados, métricas (padrão RED/USE) e tracing distribuído. Instrumentação com OpenTelemetry, coleta com Prometheus, dashboards no Grafana e alertas baseados em SLO.

### 07 — Resiliência e Confiabilidade
SLI, SLO, SLA e error budget como mecanismo de governança. Retry com backoff exponencial, circuit breaker, graceful degradation, chaos engineering, disaster recovery (RTO/RPO) e arquiteturas multi-região.

### 08 — Modernização de Sistemas Legados
Diagnóstico de débito técnico, decisão entre rewrite/refactor/replace, Strangler Fig pattern, Anti-corruption Layer, Branch by Abstraction, migração de dados com dual-write e lazy migration.

### 09 — Arquitetura Evolutiva e Governança
Arquitetura evolutiva, fitness functions no pipeline de CI, governança lean com ADRs e guilds técnicas, débito técnico como prática contínua e migrações incrementais combinando Strangler Fig com feature flags.

### 10 — Liderança Técnica e Comunicação
Liderança por influência sem autoridade hierárquica, comunicação para múltiplos públicos (CEO, devs, CFO), CNV em code reviews e design reviews, facilitação de decisões com DACI e gestão de conflitos técnicos.
