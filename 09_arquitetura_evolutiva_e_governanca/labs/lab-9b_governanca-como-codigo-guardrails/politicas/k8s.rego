package lunalog.k8s

import rego.v1

# Guardrails para os manifests do Kubernetes: o que o comitê de arquitetura conferia na mão,
# agora como política que roda em todo pull request.
#
#   deny   bloqueia o merge
#   warn   avisa, mas não bloqueia (use --fail-on-warn para endurecer)
#
# Exceções: cada regra pode ser dispensada para uma carga de trabalho específica, mas SOMENTE por um
# registro em excecoes/excecoes.yaml, com motivo, responsável e DATA DE VALIDADE. Exceção vencida volta a reprovar.

cargas := {"Deployment", "StatefulSet", "DaemonSet"}

carga_de_trabalho if input.kind in cargas

nome := input.metadata.name

pod := input.spec.template.spec

containers := pod.containers

# ---- exceções --------------------------------------------------------------------------------

excecao(regra) := e if {
	some e in data.excecoes
	e.regra == regra
	e.carga == nome
}

excecao_vigente(regra) if {
	e := excecao(regra)
	time.parse_ns("2006-01-02", e.expira) >= time.now_ns()
}

excecao_vencida(regra) if {
	e := excecao(regra)
	time.parse_ns("2006-01-02", e.expira) < time.now_ns()
}

# Uma regra só é cobrada se não houver exceção vigente para a carga.
cobrada(regra) if not excecao_vigente(regra)

msg_vencida(regra) := sprintf("%s: a excecao da regra '%s' venceu em %s; renove com justificativa ou corrija", [nome, regra, excecao(regra).expira])

# ---- regras --------------------------------------------------------------------------------

# 1. Todo contêiner declara limites de CPU e memória.
deny contains msg if {
	carga_de_trabalho
	cobrada("sem-limites")
	some c in containers
	not c.resources.limits.cpu
	msg := sprintf("%s: o conteiner '%s' nao declara limite de CPU [sem-limites]", [nome, c.name])
}

deny contains msg if {
	carga_de_trabalho
	cobrada("sem-limites")
	some c in containers
	not c.resources.limits.memory
	msg := sprintf("%s: o conteiner '%s' nao declara limite de memoria [sem-limites]", [nome, c.name])
}

# 2. Nada de imagem com tag "latest" (ou sem tag): o deploy precisa ser reproduzível.
deny contains msg if {
	carga_de_trabalho
	cobrada("imagem-latest")
	some c in containers
	imagem_sem_versao(c.image)
	msg := sprintf("%s: a imagem '%s' nao tem versao fixa (use uma tag imutavel) [imagem-latest]", [nome, c.image])
}

imagem_sem_versao(imagem) if endswith(imagem, ":latest")

imagem_sem_versao(imagem) if not contains(imagem, ":")

# 3. Todo contêiner tem readiness probe: o tráfego só chega quando ele está pronto.
deny contains msg if {
	carga_de_trabalho
	cobrada("sem-probes")
	some c in containers
	not c.readinessProbe
	msg := sprintf("%s: o conteiner '%s' nao tem readinessProbe [sem-probes]", [nome, c.name])
}

# 4. Não roda como root.
deny contains msg if {
	carga_de_trabalho
	cobrada("roda-como-root")
	not roda_como_nao_root
	msg := sprintf("%s: o pod nao exige runAsNonRoot [roda-como-root]", [nome])
}

roda_como_nao_root if pod.securityContext.runAsNonRoot == true

roda_como_nao_root if {
	count(containers) > 0
	every c in containers {
		c.securityContext.runAsNonRoot == true
	}
}

# 5. Toda carga de trabalho tem um dono (para saber quem chamar quando algo falhar).
deny contains msg if {
	carga_de_trabalho
	cobrada("sem-dono")
	not input.metadata.labels["lunalog.io/dono"]
	msg := sprintf("%s: falta o label lunalog.io/dono [sem-dono]", [nome])
}

# 6. Exceção vencida reprova de novo, com uma mensagem que diz o que aconteceu.
deny contains msg if {
	carga_de_trabalho
	some regra in {"sem-limites", "imagem-latest", "sem-probes", "roda-como-root", "sem-dono"}
	excecao_vencida(regra)
	msg := msg_vencida(regra)
}

# ---- avisos (não bloqueiam) -----------------------------------------------------------------

warn contains msg if {
	carga_de_trabalho
	input.spec.replicas == 1
	msg := sprintf("%s: apenas 1 replica; uma queda do pod e uma indisponibilidade [replica-unica]", [nome])
}
