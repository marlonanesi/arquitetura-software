# Exercício: reescreva cinco comentários de code review

Cada comentário abaixo é **real o bastante** para ter acontecido na LunaLog. Para cada um:

1. Separe o que é **observação** do que é **julgamento**.
2. Reescreva com os quatro passos (observação, sentimento, necessidade, pedido). Escreva em voz alta: soa como alguém que você gostaria de ouvir?
3. Compare com o gabarito (`gabarito.md`) **só depois**.

Tempo sugerido: 3 minutos por comentário.

---

### Comentário 1

> "Esse código está horrível, parece que foi feito às pressas."

*Contexto:* uma função de cálculo de frete, de 230 linhas, em um PR de um desenvolvedor com três meses de casa.

### Comentário 2

> "De novo sem teste? Assim não dá."

*Contexto:* o PR adiciona um novo caminho de erro no serviço de rastreamento, sem nenhum teste.

### Comentário 3

> "Isso é over-engineering. Ninguém precisa de três camadas para isso."

*Contexto:* um PR que cria uma interface, uma fábrica e uma implementação para uma consulta simples.

### Comentário 4

> "Já falei mil vezes que não pode usar `SELECT *`."

*Contexto:* um PR em um serviço que fala com um banco compartilhado, com uma consulta `SELECT *` em uma tabela com 40 colunas.

### Comentário 5

> "Discordo totalmente dessa decisão. Vai dar problema, e quando der não diga que não avisei."

*Contexto:* uma discussão sobre trocar o provedor de filas, no canal da equipe, depois que o tech lead publicou o ADR.

---

## Perguntas para a discussão em grupo

1. O que mudou na **informação técnica** entre o original e a sua reescrita? (Resposta esperada: nada, ou mais.)
2. O que mudou no **efeito provável** sobre quem recebe?
3. Em qual dos cinco foi mais difícil encontrar a observação? Por quê?
4. Que comentário seu, recente, você reescreveria?
