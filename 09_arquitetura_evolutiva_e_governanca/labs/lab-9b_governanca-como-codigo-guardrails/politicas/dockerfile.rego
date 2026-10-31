package lunalog.dockerfile

import rego.v1

# Guardrails para Dockerfiles. O Conftest entrega o Dockerfile como uma lista de instruções:
#   input[i] = {"Cmd": "from", "Value": ["imagem:tag"]}, {"Cmd": "user", "Value": ["app"]} ...

# 1. A imagem base tem versão fixa (nada de :latest nem de imagem sem tag).
deny contains msg if {
	some i
	input[i].Cmd == "from"
	imagem := input[i].Value[0]
	imagem != "scratch"
	not contains(imagem, "AS")
	sem_versao(imagem)
	msg := sprintf("a imagem base '%s' nao tem versao fixa [base-latest]", [imagem])
}

sem_versao(imagem) if endswith(imagem, ":latest")

sem_versao(imagem) if not contains(imagem, ":")

# 2. O contêiner não roda como root: tem de existir um USER, e não pode ser root.
deny contains msg if {
	count([i | some i; input[i].Cmd == "user"]) == 0
	msg := "o Dockerfile nao define USER: o processo roda como root [sem-user]"
}

deny contains msg if {
	some i
	input[i].Cmd == "user"
	input[i].Value[0] in {"root", "0"}
	msg := "o Dockerfile define USER root [user-root]"
}

# 3. Nada de ADD com URL (conteúdo remoto sem verificação).
deny contains msg if {
	some i
	input[i].Cmd == "add"
	startswith(input[i].Value[0], "http")
	msg := sprintf("ADD com URL '%s': baixe com verificacao de integridade [add-url]", [input[i].Value[0]])
}
