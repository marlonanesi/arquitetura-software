# Guia rápido: feedback técnico com os quatro passos da CNV

A Comunicação Não Violenta tem quatro passos. Em um comentário de code review ou de design review, eles ficam assim:

| Passo | Pergunta | Exemplo | Armadilha comum |
|---|---|---|---|
| **1. Observação** | O que, concretamente, eu **vi** (sem julgar)? | "A função `calcular_frete` tem 230 linhas e seis responsabilidades." | Misturar com avaliação: "está uma bagunça" |
| **2. Sentimento** | O que **isso me faz sentir ou temer** (sobre o trabalho, não sobre a pessoa)? | "Fico preocupado com a manutenção." | Sentimento disfarçado de acusação: "me sinto desrespeitado por você ter ignorado..." |
| **3. Necessidade** | Que **necessidade minha** está por trás (clareza, segurança, previsibilidade, colaboração)? | "Preciso que o próximo diagnóstico de um bug seja rápido." | Esconder a necessidade e dar só a ordem |
| **4. Pedido** | O que eu **peço**, de forma concreta e que se possa recusar? | "Faz sentido extrair cada responsabilidade para a sua função?" | Disfarçar uma exigência de pergunta: "você não acha que devia...?" |

## O padrão de uma frase

> "Quando eu **vejo** [observação], eu **me preocupo / fico inseguro / fico com dúvida** [sentimento], porque **preciso de** [necessidade]. **Você pode / faz sentido** [pedido]?"

Nem todo comentário precisa dos quatro passos. Os dois mais importantes são o **primeiro** (observar sem julgar) e o **último** (pedir algo concreto).

## O que NÃO é CNV

- **Não é ser "bonzinho".** O comentário continua apontando o problema técnico real; só o descreve de um jeito que não ataca a pessoa.
- **Não é suavizar demais.** "Talvez, quem sabe, se você quiser..." esconde o pedido. Um pedido claro respeita mais.
- **Não é uma técnica de manipulação.** Se a intenção é vencer a discussão, as palavras suaves não escondem isso.

## Como distinguir observação de julgamento

| Julgamento | Observação |
|---|---|
| "Esse código está horrível" | "Essa função tem 230 linhas e quatro níveis de `if` aninhados" |
| "Você sempre esquece os testes" | "Este PR não inclui testes para o caminho de erro" |
| "Isso é over-engineering" | "Há três camadas de abstração para uma única implementação" |
| "A sua ideia não vai escalar" | "Com 10 mil requisições por segundo, esta consulta faz uma leitura de disco por requisição" |
| "Você não ouviu o time" | "Quando o Diego propôs a alternativa, não houve resposta no PR" |
