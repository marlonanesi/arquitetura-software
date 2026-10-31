# Sessão de decisão: agenda de 60 minutos

> Use com o cronômetro (`cronometro.html`). Cada bloco tem um tempo **máximo**; quem conduz (o Driver) é o dono do relógio.
> Pré-requisito: o DACI preenchido e enviado com o convite (`01_daci/`).

| # | Minutos | Bloco | O que acontece | Quem conduz |
|---|---|---|---|---|
| 1 | 5 | Abertura | O Driver lê a decisão, o prazo, os papéis e os critérios combinados. O Approver confirma que decidirá hoje. Combina-se como será a sessão (uma pessoa fala por vez; sem notebooks abertos). | Driver |
| 2 | 10 | Contexto e dados | Apresentação **sem defender nada**: o que sabemos, os resultados da prova de conceito, os números. Perguntas só para esclarecer, não para discordar. | Driver, com os dados |
| 3 | 15 | Posições | Cada Contributor fala **3 minutos**, sem interrupção: sua posição, o que mais pesa para ele e **qual critério** está em jogo. O Driver anota no quadro, por critério. | Cada contributor |
| 4 | 15 | Discussão por critério | Passa-se critério a critério (não opção a opção): "neste critério, qual opção é melhor, e por quê?". Cada argumento é registrado no ADR **ao vivo**. | Driver |
| 5 | 5 | Preocupações e riscos | Rodada rápida: "qual é o seu maior receio com cada opção?". O que for relevante vira consequência no ADR. | Driver |
| 6 | 5 | Decisão | O Approver diz a decisão e **por quê**, em voz alta. Os demais confirmam se foram ouvidos (não se concordam). | Approver |
| 7 | 5 | Fechamento | O ADR é lido em voz alta, com o Driver como relator. Combinam-se os próximos passos, os responsáveis e a quem avisar. | Driver |

## Regras da sessão

1. **Decidir é diferente de concordar.** O objetivo é uma decisão clara e compreendida, não unanimidade. "Discordo e me comprometo" é um resultado válido.
2. **O Approver decide, depois de ouvir.** Ele não decide antes, nem divide a decisão com o grupo.
3. **Critério antes de opção.** Discutir "Istio ou Linkerd" sem critérios vira disputa de preferência. Discutir "qual atende melhor o requisito de mTLS" vira análise.
4. **Se o tempo acabar sem decisão**, o Approver decide com o que existe, ou marca a pergunta exata que falta (com responsável e data). "Vamos pensar mais" não é um resultado.
5. **A decisão é do papel, não da pessoa.** O ADR registra o que se decidiu e por quê, e as pessoas podem mudar.

## Se a conversa esquentar

- Volte ao critério: "qual critério da lista isso afeta?".
- Peça a observação, sem julgamento: "o que, concretamente, você viu que te preocupa?" (veja `03_feedback_cnv/`).
- Separe o fato da interpretação, e a solução da necessidade: "o que você precisa que seja verdade para esta opção funcionar?".
- Faça uma pausa de 2 minutos. Uma pausa custa menos que uma reunião a mais.
