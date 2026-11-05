# Arquitetura de Software na Prática

Material de apoio do curso **Arquitetura de Software: Pense e Decida como Arquiteto!**.

**Curso completo na Udemy com nosso cupom mensal dinâmico:**
https://cloudforall.com.br/redirect/arquitetura-software/


Este repositório reúne o material de apoio do curso:

- **Aulas:** os slides usados em cada aula, em formato `.pdf`, na pasta `aulas/` de cada seção.
- **Laboratórios:** 37 aulas práticas (seções 01 a 09) para rodar na sua máquina, mais um kit de referência na seção 10, na pasta `labs/` de cada seção. Veja a seção [Laboratórios](#laboratórios) mais abaixo, com os pré-requisitos e o mínimo necessário da máquina.

---

## Estrutura do Repositório

```
.
├── 01_fundamentos_arquitetura_software/
│   ├── aulas/        slides em PDF
│   └── labs/         laboratórios (um lab por pasta)
├── 02_estilos_arquiteturais/
├── 03_escalabilidade_e_design_de_apis/
│   └── pratica-exemplo/   prática 3.11 (API com problemas de design, em FastAPI)
├── 04_seguranca_arquitetural/
├── 05_ci_cd_e_estrategias_de_deploy/
├── 06_observabilidade/
├── 07_confiabilidade_e_sre/
├── 08_modernizacao_de_sistemas_legados/
├── 09_arquitetura_evolutiva_e_governanca/
└── 10_lideranca_tecnica_e_soft_skills/
```

Todas as seções seguem o mesmo formato: `aulas/` com os slides e `labs/` com os laboratórios (as seções 01 a 10 têm labs).

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

---

## Laboratórios

Os laboratórios (labs) são aulas práticas: você roda na sua máquina a arquitetura discutida na aula e vê o efeito das decisões acontecendo, com comportamento e números reais. Os cenários usam a **LunaLog**, a empresa fictícia de logística e rastreamento de entregas que acompanha o curso.

São 38 labs: os **37 labs das seções 01 a 09** são aulas práticas, todas já gravadas e publicadas no curso. O **lab 10A** (seção 10) é diferente: é um **kit prático de referência**, para você usar com o seu time depois das aulas da seção, e **não tem aula gravada**.

Como funcionam:

- Cada lab fica em `<seção>/labs/lab-<id>_<nome>/` e tem um `README.md` com objetivo, arquitetura, pré-requisitos, passo a passo em cenários, como limpar tudo no fim e perguntas para pensar.
- Tudo roda **localmente, em contêineres**. Não é preciso conta em nuvem nem pagar nada.
- Os labs de Docker Compose têm cada um o seu **próprio ambiente**, então podem ser feitos em qualquer ordem. Os labs em Kind compartilham um cluster, e alguns formam uma trilha com o anterior (veja [Trilhas](#trilhas)). A linha "Ordem de estudo" no início de cada README diz o que vem antes e o que vem depois.
- Cada README traz também os **limites do lab**: o que ele simplifica de propósito em relação a um sistema real.
- Os números que aparecem nos READMEs (tempos, taxas, latências) vêm de uma execução de referência. Na sua máquina eles vão variar. O que importa é o comportamento e a ordem de grandeza.
- Os labs de segurança (4C e 4E) contêm código **inseguro de propósito**, e as senhas e tokens de todos os labs são de exemplo. Nunca copie esse código para um sistema real.

### Pré-requisitos gerais

O requisito comum a quase todos os labs é o **Docker** com Compose v2 (Docker Desktop no Windows e no macOS, ou Docker Engine no Linux). Além dele, alguns labs pedem ferramentas específicas. Cada README repete a lista do seu lab na seção "Pré-requisitos".

| Ferramenta | Quando é necessária |
|---|---|
| **Docker** (Compose v2) | Todos os labs, exceto o 10A. Nos labs 2E e 8A o Docker é opcional (há a alternativa com Python local) |
| **Bash** e `curl` | Labs com scripts em `scripts/`: 1A, 2A, 3B, 3D, 3E, 4D, 4E, 5B, 7B, 9A, 9B e 9C. No Windows, use o Git Bash ou o WSL2 |
| **kind** e **kubectl** | Labs com Kubernetes local: 2C, 2D, 3A, 4F, 5C, 5D e 7B (o 5D pede kubectl 1.31 ou superior) |
| **Helm 3** | Labs 4F e 7B (o README do 4F mostra como usar o Helm em contêiner, sem instalar) |
| **Python 3** | Labs 2E, 8A e 9B (3.12 ou superior), e no 10A (verificador). No 1A é opcional, com alternativa em Docker |
| **Git** | Labs 2E e 8A |
| **Navegador** | Labs com interface web (Keycloak, Grafana, Jaeger, RabbitMQ, Vault). O 4B depende dele |
| **Internet** | Na primeira execução de cada lab, para baixar as imagens. Alguns labs baixam também charts e instaladores (4F, 5B, 5D, 7B, 9A e 9B) |

O lab 10A (kit de facilitação) é material pronto em Markdown e HTML, sem nada para instalar.

### Mínimo necessário da máquina

O que pesa é a **memória livre para o Docker**, e ela varia muito de um lab para outro. Os valores abaixo são os declarados no README de cada lab.

| Faixa | Memória livre | Labs |
|---|---|---|
| Leve | 1 a 2 GB | 2A, 2F, 3C, 3D, 3E, 3F, 4A, 4B, 4C, 4D, 4E, 5A, 5E, 7A, 7C, 8B, 8C, 8D, 9A, 9C |
| Média | 3 a 4 GB | 2B, 5B, 6A, 6B, 6C |
| Pesada (Kubernetes com Kind) | 4 a 6 GB | 2D e 5C (4 GB), 5D (5 GB), 2C, 3A, 4F e 7B (6 GB) |
| Não declarada no README do lab | - | 1A, 3B, 8A, 9B, 10A |

Recomendação para a máquina:

| | Mínimo | Recomendado |
|---|---|---|
| Memória (RAM) do computador | 8 GB, fazendo um lab por vez e fechando outros programas | 16 GB (necessário para ficar com folga nos labs com Kind) |
| Processador | 4 núcleos | 4 núcleos ou mais (os labs com carga do k6 geram bastante tráfego) |
| Disco livre | 20 GB, se for manter as imagens de todos os labs | 20 GB ou mais (nos testes, as imagens de todos os labs somaram cerca de 18 GB; um lab isolado usa bem menos) |
| Sistema | Windows 10/11 com Docker Desktop (WSL2), Linux ou macOS | Igual |

Observações:

- **Conta a memória que o Docker enxerga, não a do computador.** No Windows com WSL2, o limite padrão costuma ser metade da RAM. Para ajustar, crie ou edite o arquivo `%UserProfile%\.wslconfig`, por exemplo `[wsl2]` e `memory=8GB` (valor a ajustar ao seu computador), e rode `wsl --shutdown` para aplicar. No Docker Desktop com macOS, o ajuste fica em Settings > Resources.
- Rode **um lab por vez** e use a seção "Como limpar" do README ao terminar. Assim a memória, as portas e o disco voltam ao normal.
- Vários labs publicam portas no seu computador (a lista está nos pré-requisitos de cada um). O cluster Kind do lab 2C ocupa as portas 8080 e 8081, então nenhum outro lab deve usá-las ao mesmo tempo.
- Para ver e recuperar espaço em disco: `docker system df` mostra o uso e `docker image prune -a` remove as imagens que nenhum contêiner está usando.
- Os labs foram desenvolvidos no Windows 11 com Docker Desktop (WSL2). Em Linux e macOS os comandos são os mesmos. Se algo se comportar de forma diferente do descrito no README, avise pela área de perguntas do curso na Udemy.
- Nos exemplos em Bash, no PowerShell use `curl.exe` no lugar de `curl`. Os labs 2B, 2C e 7C informam que os comandos funcionam também no PowerShell.

### Como começar

```bash
git clone https://github.com/marlonanesi/arquitetura-software.git
cd arquitetura-software/02_estilos_arquiteturais/labs/lab-2a_monolito-modular-vs-distribuido
```

Abra o `README.md` do lab (o exemplo acima é o lab 2A) e siga os passos na ordem. Os scripts `.sh` do repositório usam fim de linha LF (o `.gitattributes` garante isso, inclusive no Windows).

### Trilhas

Alguns labs formam uma sequência, em que um continua o cenário, o domínio ou o ambiente do anterior. Na ordem você aproveita melhor o contexto. O README de cada lab diz se ele pode ser feito sozinho e o que precisa estar pronto antes (por exemplo, o cluster Kind).

| Trilha | Sequência |
|---|---|
| Kubernetes local (Kind) | 2C, 2D, 3A, 4F, 5C, 5D, 7B (o cluster `lunalog-arq`, criado no 2C, é reaproveitado) |
| Hexagonal | 2E, 2F |
| Falhas injetadas | 3F, 7A |
| Identidade e acesso | 4B, 4C, 4D |
| Observabilidade | 6A, 6B, 6C |
| Modernização do legado | 8B, 8C, 8D, 9C |

### Aulas gravadas dos labs

Os labs das seções 01 a 09 estão **concluídos**: os 37 têm aula gravada e publicada na Udemy, explicando o lab passo a passo. O lab 10A é um kit de referência e não tem aula gravada: o README dele traz tudo o que você precisa para usar o material. A coluna **Aula na Udemy** da lista abaixo mostra a situação de cada lab. Todos os READMEs funcionam por conta própria, com ou sem a aula. Se algum lab for atualizado, a mudança entra aqui no repositório.

### Lista de labs

| Seção | Lab | Tema | Ambiente | Aula na Udemy |
|---|---|---|---|---|
| 01 | [1A](01_fundamentos_arquitetura_software/labs/lab-1a_arquitetura-como-codigo-c4-e-adr/) | Arquitetura como código: C4 e ADR versionados | Compose e Python | Publicada |
| 02 | [2A](02_estilos_arquiteturais/labs/lab-2a_monolito-modular-vs-distribuido/) | Monólito modular e monólito distribuído lado a lado | Compose | Publicada |
| 02 | [2B](02_estilos_arquiteturais/labs/lab-2b_eda-ordem-idempotencia-e-dlq/) | EDA na prática: ordem, idempotência e dead-letter queue | Compose | Publicada |
| 02 | [2C](02_estilos_arquiteturais/labs/lab-2c_kind-stateless-e-health-checks/) | Kubernetes local com Kind: stateless, imagem imutável e health checks | Kind | Publicada |
| 02 | [2D](02_estilos_arquiteturais/labs/lab-2d_pod-patterns-sidecar-ambassador-adapter/) | Padrões de pod: sidecar, ambassador e adapter | Kind | Publicada |
| 02 | [2E](02_estilos_arquiteturais/labs/lab-2e_hexagonal-portas-e-adaptadores/) | Arquitetura hexagonal: trocando o adaptador sem tocar no domínio | Python local (Docker opcional) | Publicada |
| 02 | [2F](02_estilos_arquiteturais/labs/lab-2f_cqrs-e-event-sourcing/) | CQRS e Event Sourcing sobre o domínio hexagonal | Compose | Publicada |
| 03 | [3A](03_escalabilidade_e_design_de_apis/labs/lab-3a_hpa-escala-horizontal/) | Escala horizontal no Kind: HPA sob carga e o custo do estado local | Kind | Publicada |
| 03 | [3B](03_escalabilidade_e_design_de_apis/labs/lab-3b_load-balancing-algoritmos-l4-l7/) | Load balancing: algoritmos, afinidade de sessão e camadas L4 e L7 | Compose | Publicada |
| 03 | [3C](03_escalabilidade_e_design_de_apis/labs/lab-3c_cache-aside-stampede-e-jitter/) | Cache-aside, cache stampede e TTL com jitter | Compose | Publicada |
| 03 | [3D](03_escalabilidade_e_design_de_apis/labs/lab-3d_filas-absorvendo-picos/) | Filas absorvendo picos: escrita direta versus fila | Compose | Publicada |
| 03 | [3E](03_escalabilidade_e_design_de_apis/labs/lab-3e_rate-limiting-algoritmos/) | Rate limiting: janela fixa, janela deslizante e token bucket | Compose | Publicada |
| 03 | [3F](03_escalabilidade_e_design_de_apis/labs/lab-3f_circuit-breaker-e-bulkhead/) | Circuit breaker e bulkhead com falhas injetadas | Compose | Publicada |
| 04 | [4A](04_seguranca_arquitetural/labs/lab-4a_vault-envelope-encryption-e-rotacao/) | Envelope encryption, rotação de chaves e credenciais dinâmicas com Vault | Compose | Publicada |
| 04 | [4B](04_seguranca_arquitetural/labs/lab-4b_oidc-pkce-com-keycloak/) | OAuth 2.1 e OpenID Connect: Authorization Code com PKCE passo a passo | Compose | Publicada |
| 04 | [4C](04_seguranca_arquitetural/labs/lab-4c_jwt-armadilhas/) | JWT: ataques reproduzíveis e validação correta | Compose | Publicada |
| 04 | [4D](04_seguranca_arquitetural/labs/lab-4d_policy-as-code-opa-e-openfga/) | Policy-as-code: a mesma regra em RBAC, ABAC e ReBAC com OPA e OpenFGA | Compose | Publicada |
| 04 | [4E](04_seguranca_arquitetural/labs/lab-4e_stride-sistema-inseguro/) | STRIDE na prática: diagnóstico e redesign de um sistema inseguro | Compose | Publicada |
| 04 | [4F](04_seguranca_arquitetural/labs/lab-4f_zero-trust-mtls-no-kind/) | Zero trust no Kind: mTLS automático e autorização entre serviços | Kind e Istio | Publicada |
| 05 | [5A](05_ci_cd_e_estrategias_de_deploy/labs/lab-5a_contract-testing-com-pact/) | Consumer-driven contracts com Pact | Compose | Publicada |
| 05 | [5B](05_ci_cd_e_estrategias_de_deploy/labs/lab-5b_pipeline-maduro-antes-e-depois/) | Pipeline CI/CD: do pipeline com problemas ao pipeline maduro | GitHub Actions, com simulação local em Docker | Publicada |
| 05 | [5C](05_ci_cd_e_estrategias_de_deploy/labs/lab-5c_blue-green-e-rolling-no-kind/) | Blue/green e rolling update no Kind | Kind | Publicada |
| 05 | [5D](05_ci_cd_e_estrategias_de_deploy/labs/lab-5d_canary-e-rollback-automatico/) | Canary release com análise automática e rollback | Kind | Publicada |
| 05 | [5E](05_ci_cd_e_estrategias_de_deploy/labs/lab-5e_expand-contract-migracao-reversivel/) | Expand-contract: migração de schema reversível em quatro fases | Compose | Publicada |
| 06 | [6A](06_observabilidade/labs/lab-6a_opentelemetry-ponta-a-ponta/) | OpenTelemetry ponta a ponta: logs, métricas e traces | Compose | Publicada |
| 06 | [6B](06_observabilidade/labs/lab-6b_prometheus-promql-e-grafana/) | Prometheus, PromQL e Grafana: métricas RED e dashboard efetivo | Compose | Publicada |
| 06 | [6C](06_observabilidade/labs/lab-6c_alertas-por-slo-burn-rate/) | Alertas por SLO: burn rate e error budget | Compose | Publicada |
| 07 | [7A](07_confiabilidade_e_sre/labs/lab-7a_retry-timeout-backoff-e-fallback/) | Retry, timeout, backoff e fallback sob falha | Compose | Publicada |
| 07 | [7B](07_confiabilidade_e_sre/labs/lab-7b_chaos-engineering-no-kind/) | Chaos engineering no Kind: hipótese, experimento e resultado | Kind e Chaos Mesh | Publicada |
| 07 | [7C](07_confiabilidade_e_sre/labs/lab-7c_disaster-recovery-rto-rpo/) | Disaster recovery: restore no tempo, standby e medição de RTO e RPO | Compose | Publicada |
| 08 | [8A](08_modernizacao_de_sistemas_legados/labs/lab-8a_hotspots-diagnostico-de-debito/) | Diagnóstico de débito técnico por hotspots no histórico do Git | Python e Git locais (Docker opcional) | Publicada |
| 08 | [8B](08_modernizacao_de_sistemas_legados/labs/lab-8b_strangler-fig-com-proxy/) | Strangler Fig com proxy: migrando rota a rota | Compose | Publicada |
| 08 | [8C](08_modernizacao_de_sistemas_legados/labs/lab-8c_anti-corruption-layer-e-branch-by-abstraction/) | Anti-corruption layer e Branch by Abstraction | Compose | Publicada |
| 08 | [8D](08_modernizacao_de_sistemas_legados/labs/lab-8d_migracao-de-dados-dual-write/) | Migração de dados: backfill, dual-write e reconciliação | Compose | Publicada |
| 09 | [9A](09_arquitetura_evolutiva_e_governanca/labs/lab-9a_fitness-functions-no-ci/) | Fitness functions no CI: acoplamento, desempenho, segurança e compatibilidade | GitHub Actions, com simulação local em Docker | Publicada |
| 09 | [9B](09_arquitetura_evolutiva_e_governanca/labs/lab-9b_governanca-como-codigo-guardrails/) | Governança como código: ADRs validados e guardrails de build | Docker e Python | Publicada |
| 09 | [9C](09_arquitetura_evolutiva_e_governanca/labs/lab-9c_migracao-incremental-ponta-a-ponta/) | Migração incremental ponta a ponta: marcos, flags e critérios de rollback | Compose | Publicada |
| 10 | [10A](10_lideranca_tecnica_e_soft_skills/labs/lab-10a_kit-de-facilitacao-daci-adr-e-cnv/) | Kit de facilitação: DACI, ADR ao vivo e reescrita de code review com CNV | Material pronto, sem instalação | Sem aula (kit de referência) |
