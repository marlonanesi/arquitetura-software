package lunalog.abac

import rego.v1

# ABAC: a decisão usa ATRIBUTOS do usuário, do recurso e do contexto (a hora).
#   usuário  : cargo, transportadora, filial            (vêm do diretório de usuários, data.usuarios)
#   recurso  : transportadora, filial, motorista        (vêm de quem consulta, no input)
#   contexto : hora                                     (vem no input)

default allow := false

usuario := data.usuarios[input.usuario]

# O auditor da plataforma vê tudo.
allow if {
	input.acao == "ver"
	usuario.cargo == "auditor"
}

# O gerente vê as rotas de todas as filiais da sua transportadora.
allow if {
	input.acao == "ver"
	usuario.cargo == "gerente"
	usuario.transportadora == input.recurso.transportadora
}

# O operador vê as rotas da sua filial, em horário comercial (6h às 22h).
allow if {
	input.acao == "ver"
	usuario.cargo == "operador"
	usuario.transportadora == input.recurso.transportadora
	usuario.filial == input.recurso.filial
	input.hora >= 6
	input.hora < 22
}

# O motorista vê apenas as rotas atribuídas a ele.
allow if {
	input.acao == "ver"
	usuario.cargo == "motorista"
	input.recurso.motorista == input.usuario
}
