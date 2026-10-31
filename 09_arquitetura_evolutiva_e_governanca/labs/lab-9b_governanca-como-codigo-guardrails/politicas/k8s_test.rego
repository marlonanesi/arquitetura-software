package lunalog.k8s_test

import data.lunalog.k8s
import rego.v1

# Testes das políticas: uma política é código, e código tem teste.

bom := {
	"kind": "Deployment",
	"metadata": {"name": "rastreamento", "labels": {"lunalog.io/dono": "time-rastreamento"}},
	"spec": {"replicas": 3, "template": {"spec": {
		"securityContext": {"runAsNonRoot": true},
		"containers": [{
			"name": "app",
			"image": "lunalog/rastreamento:1.4.2",
			"resources": {"limits": {"cpu": "500m", "memory": "256Mi"}},
			"readinessProbe": {"httpGet": {"path": "/saude", "port": 8000}},
		}],
	}}},
}

test_manifest_conforme_nao_tem_reprovacao if {
	count(k8s.deny) == 0 with input as bom
}

test_sem_limite_de_cpu_reprova if {
	ruim := json.patch(bom, [{"op": "remove", "path": "/spec/template/spec/containers/0/resources/limits/cpu"}])
	some m in k8s.deny with input as ruim
	contains(m, "sem-limites")
}

test_imagem_latest_reprova if {
	ruim := json.patch(bom, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "lunalog/rastreamento:latest"}])
	some m in k8s.deny with input as ruim
	contains(m, "imagem-latest")
}

test_imagem_sem_tag_reprova if {
	ruim := json.patch(bom, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "lunalog/rastreamento"}])
	some m in k8s.deny with input as ruim
	contains(m, "imagem-latest")
}

test_sem_readiness_reprova if {
	ruim := json.patch(bom, [{"op": "remove", "path": "/spec/template/spec/containers/0/readinessProbe"}])
	some m in k8s.deny with input as ruim
	contains(m, "sem-probes")
}

test_sem_run_as_non_root_reprova if {
	ruim := json.patch(bom, [{"op": "remove", "path": "/spec/template/spec/securityContext"}])
	some m in k8s.deny with input as ruim
	contains(m, "roda-como-root")
}

test_sem_dono_reprova if {
	ruim := json.patch(bom, [{"op": "remove", "path": "/metadata/labels"}])
	some m in k8s.deny with input as ruim
	contains(m, "sem-dono")
}

test_replica_unica_apenas_avisa if {
	uma := json.patch(bom, [{"op": "replace", "path": "/spec/replicas", "value": 1}])
	count(k8s.deny) == 0 with input as uma
	count(k8s.warn) == 1 with input as uma
}

test_excecao_vigente_dispensa_a_regra if {
	ruim := json.patch(bom, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "terceiro/relatorios:latest"}])
	ruim2 := json.patch(ruim, [{"op": "replace", "path": "/metadata/name", "value": "legado-relatorios"}])
	excecoes := [{"regra": "imagem-latest", "carga": "legado-relatorios", "expira": "2100-12-31"}]
	count(k8s.deny) == 0 with input as ruim2 with data.excecoes as excecoes
}

test_excecao_vencida_reprova_de_novo if {
	ruim := json.patch(bom, [{"op": "replace", "path": "/spec/template/spec/containers/0/image", "value": "terceiro/relatorios:latest"}])
	ruim2 := json.patch(ruim, [{"op": "replace", "path": "/metadata/name", "value": "legado-relatorios"}])
	excecoes := [{"regra": "imagem-latest", "carga": "legado-relatorios", "expira": "2020-01-01"}]
	some m in k8s.deny with input as ruim2 with data.excecoes as excecoes
	contains(m, "venceu em 2020-01-01")
}
