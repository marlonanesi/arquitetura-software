# ADR ao vivo: roteiro de captura

> O Driver abre este arquivo em uma tela compartilhada e o preenche **durante a sessão**, não depois. Todos veem o que está sendo registrado e corrigem na hora ("não foi isso que eu disse"). Isso reduz a discussão sobre a ata depois da reunião.

Copie o modelo abaixo para `adrs/NNNN-titulo.md` e preencha nos momentos indicados.

```markdown
---
status: proposed                      # (bloco 1) começa como proposta; vira accepted no bloco 6
date: AAAA-MM-DD                      # (bloco 1) data da sessão
decision-makers: Approver, Driver     # (bloco 1) quem decide e quem conduz
---
# NNNN. <a decisão, como afirmação>   # (bloco 6) escreva o título só depois de decidir

## Contexto e problema

<o que força a decisão agora, em 2 ou 3 frases>      # (bloco 1 e 2) da pauta e dos dados apresentados

## Critérios

* <critério 1>                                        # (bloco 1) combinados antes de discutir
* <critério 2>

## Alternativas consideradas

* <Opção A>: <a favor / contra, por critério>         # (blocos 3 e 4) os argumentos entram AO VIVO
* <Opção B>: <a favor / contra, por critério>

## Decisão

<o que foi decidido e por quê, nas palavras do Approver>   # (bloco 6)

## Consequências

* Bom, porque ...                                     # (bloco 5) as preocupações viram consequências
* Ruim, porque ...
* Riscos e como vamos acompanhar: ...
```

## Dicas de captura

- **Escreva o argumento, não a pessoa.** "A malha completa autoriza por identidade" é um argumento; "o Diego prefere o Istio" é uma preferência.
- **Cada contra vira uma consequência ou um plano**, não um item esquecido.
- **Se uma discordância permanece, registre-a** em "Consequências" ("Camila registrou a preocupação X; revisitaremos em AAAA-MM"). Registrar a discordância é parte de ouvi-la.
- **Status**: `proposed` até o Approver decidir; depois, `accepted` (ou `rejected`). Valide com o validador de ADRs do lab 1A ou do 9B.
