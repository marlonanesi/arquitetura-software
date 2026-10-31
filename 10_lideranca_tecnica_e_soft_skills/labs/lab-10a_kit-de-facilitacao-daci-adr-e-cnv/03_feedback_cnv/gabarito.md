# Gabarito: cinco comentários reescritos

> Não é a única resposta certa. O critério é: **mesma informação técnica ou mais, sem julgamento sobre a pessoa, com um pedido concreto**.

---

### Comentário 1

**Original:** "Esse código está horrível, parece que foi feito às pressas."

**O que é julgamento:** "horrível", "às pressas" (uma suposição sobre o autor).
**Observação:** a função `calcular_frete` tem 230 linhas e mistura seis responsabilidades (validação, tabela de tarifas, desconto, imposto, arredondamento e log).

**Reescrito:**
> "Identifiquei seis responsabilidades distintas em `calcular_frete` (validação, tarifa, desconto, imposto, arredondamento e log). Fico preocupado com o diagnóstico de problemas futuros: preciso que um erro no imposto seja fácil de achar sem ler 230 linhas. Faz sentido extrair cada responsabilidade para a sua própria função? Posso ajudar a desenhar a divisão, se for útil."

---

### Comentário 2

**Original:** "De novo sem teste? Assim não dá."

**O que é julgamento:** "de novo" (generaliza), "assim não dá" (ameaça sem conteúdo).
**Observação:** este PR acrescenta o caminho de erro `ErroDeCotacao` em `rastreamento.py` e não inclui testes para ele.

**Reescrito:**
> "Este PR acrescenta o caminho de erro `ErroDeCotacao`, e não vi testes cobrindo-o. Fico inseguro de aprovar sem ele, porque preciso ter certeza de que a falha não vai chegar à produção sem ser notada. Você consegue acrescentar um teste para o caso em que a cotação expira? Se faltar tempo hoje, podemos combinar o teste em um PR logo em seguida, com data."

---

### Comentário 3

**Original:** "Isso é over-engineering. Ninguém precisa de três camadas para isso."

**O que é julgamento:** "over-engineering" (um rótulo), "ninguém precisa".
**Observação:** há uma interface, uma fábrica e uma única implementação para a consulta de tarifas.

**Reescrito:**
> "Vejo uma interface, uma fábrica e uma única implementação para a consulta de tarifas. Fico em dúvida se essas camadas pagam o seu custo agora, porque preciso que o código seja fácil de ler para quem chegar depois. Existe uma segunda implementação prevista que justifique a interface? Se não, você aceitaria começar só com a implementação e extrair a interface quando ela aparecer?"

---

### Comentário 4

**Original:** "Já falei mil vezes que não pode usar `SELECT *`."

**O que é julgamento:** "mil vezes" (um reproche), "não pode" (sem razão).
**Observação:** a consulta usa `SELECT *` em uma tabela de 40 colunas, em um banco compartilhado com o serviço de relatórios.

**Reescrito:**
> "A consulta usa `SELECT *` em uma tabela de 40 colunas do banco compartilhado. Fico preocupado: se alguém acrescentar uma coluna, este serviço passa a trazer dados que não precisa, e o relatório pode ficar lento. Preciso de previsibilidade na carga do banco. Você pode listar só as colunas que usa? Nós também podemos acrescentar uma regra no linter para avisar disso automaticamente, para não depender de lembrar em cada PR."

(Observe a **última frase**: se o problema se repete, o pedido mais honesto é por um **guardrail**, não por mais reprimendas. É o tema do lab 9B.)

---

### Comentário 5

**Original:** "Discordo totalmente dessa decisão. Vai dar problema, e quando der não diga que não avisei."

**O que é julgamento:** "totalmente", "vai dar problema" (profecia), "não diga que não avisei" (ameaça futura).
**Observação:** o ADR 0009 escolhe o broker X, e o requisito de ordenação por chave não está nos critérios.

**Reescrito:**
> "Li o ADR 0009. Os critérios não incluem ordenação por chave, que o serviço de rastreamento exige. Fico preocupado de descobrirmos isso só depois do deploy. Preciso que o requisito esteja coberto antes de seguirmos. Podemos acrescentar esse critério e medir os dois brokers contra ele, em uma conversa de 20 minutos amanhã? Se o resultado não mudar a decisão, eu apoio e me comprometo."

(Note o "se não mudar, eu apoio e me comprometo": discordar e se comprometer é um resultado legítimo da sessão de decisão.)

---

## O que se repete nos cinco

1. **A informação técnica foi preservada** (seis responsabilidades, caminho de erro sem teste, 40 colunas, critério ausente), e em alguns casos **ficou mais precisa**.
2. **O julgamento sobre a pessoa saiu** ("horrível", "de novo", "mil vezes", "não diga que não avisei").
3. Cada comentário termina em um **pedido concreto e recusável**, com uma saída possível.
4. A reescrita é **mais longa**. Isso é um custo real: vale em comentários que importam, e dispensa-se em um "nit" (um detalhe) óbvio.
