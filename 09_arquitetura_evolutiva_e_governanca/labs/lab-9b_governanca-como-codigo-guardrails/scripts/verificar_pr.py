"""Confere se a descrição de um pull request traz o checklist arquitetural PREENCHIDO.

  python verificar_pr.py corpo-do-pr.md

No GitHub Actions, o corpo do PR vem de github.event.pull_request.body (veja ci/governanca.yml).
Regra: todos os itens do template precisam existir e estar marcados ([x]). Um item que não se aplica deve ser
marcado com uma justificativa, nunca apagado. A máquina confere que o checklist foi LIDO, não que a resposta
é verdadeira: quem confere a verdade é o revisor humano (o CODEOWNERS).
"""
import re
import sys

ITENS = ["Decisão registrada", "Reversibilidade", "Segurança e dados", "Operação", "Exceções"]

texto = open(sys.argv[1], encoding="utf-8").read()
problemas = []
for item in ITENS:
    m = re.search(rf"- \[( |x|X)\] \*\*{re.escape(item)}", texto)
    if m is None:
        problemas.append(f"falta o item '{item}' do checklist (use o modelo em modelos/pull_request_template.md)")
    elif m.group(1) == " ":
        problemas.append(f"o item '{item}' do checklist nao foi marcado")

if problemas:
    print(f"{len(problemas)} pendencia(s) no checklist do pull request:")
    for p in problemas:
        print(f"  - {p}")
    sys.exit(1)
print("checklist arquitetural completo")
