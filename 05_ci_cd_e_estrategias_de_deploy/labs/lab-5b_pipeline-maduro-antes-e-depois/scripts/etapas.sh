#!/usr/bin/env bash
# As etapas do pipeline, uma função por etapa. Tanto os workflows do GitHub Actions quanto o
# simulador local chamam as mesmas funções, então "o que roda" é idêntico nos dois lugares.
#
# Uso: bash scripts/etapas.sh <etapa> [argumentos]
# Etapas: lint, testes, segredos, sast, sca, construir, scan_imagem, publicar, deploy, smoke, parar
set -uo pipefail
export MSYS_NO_PATHCONV=1   # evita que o Git Bash do Windows reescreva caminhos de contêiner

RAIZ="${RAIZ:-$(cd "$(dirname "$0")/.." && pwd)}"
VERSAO="${VERSAO:-0.0.0-local}"
IMAGEM="${IMAGEM:-lunalog/tracking}"
cd "$RAIZ" || exit 1

python_em_conteiner() { docker run --rm -e PIP_ROOT_USER_ACTION=ignore -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "$RAIZ":/w -w /w python:3.12-slim "$@"; }

# --- Qualidade: rápida, roda primeiro ---------------------------------------------------------
lint() {
  python_em_conteiner sh -c "pip install -q flake8==7.1.1 && flake8 app tests"
}

testes() {
  python_em_conteiner sh -c "pip install -q -r app/requirements.txt -r requirements-dev.txt && pytest -q -p no:cacheprovider --cov=app --cov-fail-under=80"
}

# --- Segurança --------------------------------------------------------------------------------
segredos() {   # procura credenciais no código
  docker run --rm -v "$RAIZ":/repo zricethezav/gitleaks:v8.21.2 detect --no-git --source /repo --redact --exit-code 1 --no-banner -l warn
}

sast() {       # análise estática do código
  docker run --rm -v "$RAIZ":/src -w /src semgrep/semgrep:1.99.0 semgrep --config semgrep-regras.yml --error --quiet --metrics off app
}

sca() {        # dependências com vulnerabilidades conhecidas
  docker run --rm -v "$RAIZ":/w -v lab5b-trivy-cache:/root/.cache aquasec/trivy:0.58.1 fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 --quiet /w/app
}

# --- Build e publicação -----------------------------------------------------------------------
construir() {
  docker build -q -t "$IMAGEM:$VERSAO" --build-arg VERSAO="$VERSAO" app > /dev/null
}

scan_imagem() { # vulnerabilidades críticas com correção disponível na imagem final
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v lab5b-trivy-cache:/root/.cache aquasec/trivy:0.58.1 image --severity CRITICAL --ignore-unfixed --exit-code 1 --quiet "$IMAGEM:$VERSAO"
}

publicar() {   # simulado: não há registry neste laboratório
  echo "[simulado] docker push $IMAGEM:$VERSAO"
}

# --- Implantação ------------------------------------------------------------------------------
# deploy <ambiente> <porta> [versao]
deploy() {
  local amb=$1 porta=$2 versao=${3:-$VERSAO}
  docker rm -f "tracking-$amb" > /dev/null 2>&1
  docker run -d --name "tracking-$amb" -p "$porta:8000" -e AMBIENTE="$amb" "$IMAGEM:$versao" > /dev/null
}

# smoke <porta>: a aplicação responde de verdade?
smoke() {
  local porta=$1
  for _ in $(seq 1 8); do
    if curl -fsS --max-time 2 "localhost:$porta/saude" > /dev/null 2>&1; then echo "smoke test ok na porta $porta"; return 0; fi
    sleep 1
  done
  echo "smoke test FALHOU na porta $porta"
  return 1
}

parar() { docker rm -f "tracking-$1" > /dev/null 2>&1; }

if [ $# -ge 1 ]; then
  etapa=$1; shift
  "$etapa" "$@"
fi
