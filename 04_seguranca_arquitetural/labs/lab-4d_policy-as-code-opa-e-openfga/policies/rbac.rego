package lunalog.rbac

import rego.v1

# RBAC: permissões por PAPEL (cargo). A pergunta que o RBAC responde é
# "este cargo pode VER rotas?", e não "este usuário pode ver ESTA rota?".

permissoes := {
	"motorista": {"ver"},
	"operador": {"ver"},
	"gerente": {"ver"},
	"auditor": {"ver"},
}

default allow := false

allow if {
	cargo := data.usuarios[input.usuario].cargo
	input.acao in permissoes[cargo]
}
