#!/usr/bin/env bash
# As fitness functions: verificações automáticas de que a arquitetura continua saudável.
# Cada função sai com código diferente de zero quando a arquitetura se degrada.
# Os workflows de CI e o simulador chamam exatamente estas funções.
#
# Uso: bash scripts/fitness.sh <acoplamento|desempenho|seguranca|compatibilidade|gerar_contrato>
set -uo pipefail
export MSYS_NO_PATHCONV=1

RAIZ="${RAIZ:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || exit 1

python_em_conteiner() { docker run --rm -e PIP_ROOT_USER_ACTION=ignore -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "$RAIZ":/w -w /w "$@"; }

# 1. ACOPLAMENTO: as regras de dependência entre camadas e módulos (arquivo app/.importlinter)
acoplamento() {
  python_em_conteiner python:3.12-slim sh -c "pip install -q import-linter==2.1 && cd app && lint-imports"
}

# 2. DESEMPENHO: o orçamento de latência (k6 com thresholds)
desempenho() {
  local rede="fitness-9a-rede" alvo="fitness-9a-app"
  docker rm -f "$alvo" > /dev/null 2>&1; docker network rm "$rede" > /dev/null 2>&1
  docker network create "$rede" > /dev/null
  docker build -q -t fitness-9a:local app > /dev/null
  docker run -d --name "$alvo" --network "$rede" fitness-9a:local > /dev/null
  for _ in $(seq 1 15); do
    docker run --rm --network "$rede" curlimages/curl:8.11.0 -fsS --max-time 2 "http://$alvo:8000/saude" > /dev/null 2>&1 && break
    sleep 1
  done
  docker run --rm --network "$rede" -e ALVO="$alvo" -v "$RAIZ/k6":/k6:ro grafana/k6:0.54.0 run --quiet /k6/orcamento.js
  local rc=$?
  docker rm -f "$alvo" > /dev/null 2>&1; docker network rm "$rede" > /dev/null 2>&1
  return $rc
}

# 3. SEGURANÇA: nenhum segredo no código e nenhuma dependência com vulnerabilidade crítica
seguranca() {
  docker run --rm -v "$RAIZ":/repo zricethezav/gitleaks:v8.21.2 detect --no-git --source /repo --redact --exit-code 1 --no-banner -l warn || return 1
  docker run --rm -v "$RAIZ":/w -v lab9a-trivy-cache:/root/.cache aquasec/trivy:0.58.1 fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 --quiet /w/app
}

# Gera a especificação OpenAPI da API atual em contrato/openapi-atual.json
gerar_contrato() {
  python_em_conteiner python:3.12-slim sh -c "pip install -q -r app/requirements.txt && cd app && python -c \"import json; from lunalog.api.rotas import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True))\" > ../contrato/openapi-atual.json"
}

# 4. COMPATIBILIDADE: a API atual não quebra quem a consome (compara com o contrato publicado, v1)
compatibilidade() {
  gerar_contrato || return 1
  docker run --rm -v "$RAIZ/contrato":/c:ro tufin/oasdiff:v1.10.25 breaking /c/openapi-v1.json /c/openapi-atual.json --fail-on ERR
}

if [ $# -ge 1 ]; then
  funcao=$1; shift
  "$funcao" "$@"
fi
