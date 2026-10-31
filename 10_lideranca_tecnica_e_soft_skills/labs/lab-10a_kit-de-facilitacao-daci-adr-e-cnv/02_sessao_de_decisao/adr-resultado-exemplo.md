---
status: accepted
date: 2026-11-12
decision-makers: Roberto, Ana
---
# 0008. Adotar o Istio como service mesh, começando por um namespace

## Contexto e problema

O cliente farmacêutico exige mTLS entre os serviços e autorização por identidade a partir do próximo trimestre. Sem uma decisão comum, cada time implementaria o seu próprio TLS, repetindo o problema das doze autorizações diferentes. Precisamos escolher uma malha de serviços em uma sessão de 60 minutos, com a prova de conceito (lab 4F) já feita.

## Critérios

* Atender o requisito de mTLS com identidade por serviço e certificados de curta duração.
* Custo de operar (pessoas-hora por mês e memória por pod).
* Autorização por identidade (quem pode chamar quem), em nível de método.
* Reversibilidade: quanto custa desistir depois.

## Alternativas consideradas

* **Istio**: atende todos os critérios de segurança, inclusive autorização por identidade e por método. É mais complexo de operar e consome mais recursos.
* **Linkerd**: mais simples e leve, atende o mTLS, mas a autorização por política é mais limitada, e o requisito de autorização por método exigiria complementos.

## Decisão

Adotar o **Istio**, em modo estrito de mTLS e com autorização por identidade, começando por **um namespace** (o de rastreamento). O Roberto decidiu porque a autorização por identidade e por método é um requisito contratual, e o Linkerd exigiria complementos que somariam complexidade de qualquer forma. A Camila (segurança) foi decisiva ao mostrar que o requisito de autorização por método não era opcional.

## Consequências

* Bom, porque o requisito de mTLS e de autorização por identidade fica atendido por uma só ferramenta, com políticas versionadas.
* Ruim, porque aumenta o custo de operação: o Diego estima uma pessoa-semana de capacitação e cerca de 100 MB a mais de memória por pod.
* Risco: complexidade operacional. Mitigação: começar por um namespace, medir o custo real por 4 semanas e decidir a expansão em uma nova sessão.
* O Diego registrou a preocupação com o custo de operação; será revisitada em 2026-12 com os números reais.
