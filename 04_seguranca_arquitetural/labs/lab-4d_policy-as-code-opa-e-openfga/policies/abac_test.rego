package lunalog.abac_test

import data.lunalog.abac
import rego.v1

# Testes unitários da política. Rodam com "opa test" e entram no pipeline de CI,
# como qualquer outro código: uma mudança de política que quebra uma regra não passa.

usuarios := {
	"ana": {"cargo": "operador", "transportadora": "rapido", "filial": "sp"},
	"bruno": {"cargo": "motorista", "transportadora": "rapido", "filial": "sp"},
	"carla": {"cargo": "motorista", "transportadora": "veloz", "filial": "sp"},
	"dora": {"cargo": "gerente", "transportadora": "rapido"},
	"eva": {"cargo": "auditor"},
}

rota_r1 := {"transportadora": "rapido", "filial": "sp", "motorista": "bruno"}

rota_r2 := {"transportadora": "rapido", "filial": "rj", "motorista": "fabio"}

rota_r3 := {"transportadora": "veloz", "filial": "sp", "motorista": "carla"}

test_motorista_ve_a_propria_rota if {
	abac.allow with input as {"usuario": "bruno", "acao": "ver", "recurso": rota_r1, "hora": 10} with data.usuarios as usuarios
}

test_motorista_nao_ve_rota_de_outro_motorista if {
	not abac.allow with input as {"usuario": "bruno", "acao": "ver", "recurso": rota_r3, "hora": 10} with data.usuarios as usuarios
}

test_gerente_ve_todas_as_filiais_da_sua_transportadora if {
	abac.allow with input as {"usuario": "dora", "acao": "ver", "recurso": rota_r1, "hora": 10} with data.usuarios as usuarios
	abac.allow with input as {"usuario": "dora", "acao": "ver", "recurso": rota_r2, "hora": 10} with data.usuarios as usuarios
}

test_gerente_nao_ve_outra_transportadora if {
	not abac.allow with input as {"usuario": "dora", "acao": "ver", "recurso": rota_r3, "hora": 10} with data.usuarios as usuarios
}

test_operador_ve_a_propria_filial if {
	abac.allow with input as {"usuario": "ana", "acao": "ver", "recurso": rota_r1, "hora": 10} with data.usuarios as usuarios
}

test_operador_nao_ve_outra_filial if {
	not abac.allow with input as {"usuario": "ana", "acao": "ver", "recurso": rota_r2, "hora": 10} with data.usuarios as usuarios
}

test_operador_nao_ve_fora_do_horario_comercial if {
	not abac.allow with input as {"usuario": "ana", "acao": "ver", "recurso": rota_r1, "hora": 23} with data.usuarios as usuarios
}

test_auditor_ve_tudo if {
	abac.allow with input as {"usuario": "eva", "acao": "ver", "recurso": rota_r3, "hora": 10} with data.usuarios as usuarios
}

test_ninguem_edita if {
	not abac.allow with input as {"usuario": "dora", "acao": "editar", "recurso": rota_r1, "hora": 10} with data.usuarios as usuarios
}
