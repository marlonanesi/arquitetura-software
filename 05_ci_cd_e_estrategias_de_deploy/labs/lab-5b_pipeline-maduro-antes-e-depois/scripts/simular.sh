#!/usr/bin/env bash
# Simulador local dos dois pipelines: executa, na sua máquina, a mesma sequência de etapas dos
# workflows de antes/pipeline.yml e depois/pipeline.yml, com cronometragem por etapa.
#
# Uso: bash scripts/simular.sh <antes|depois> [mudanca]
# Mudanças: teste-quebrado, codigo-inseguro, dependencia-vulneravel, segredo-no-codigo, falha-so-em-producao
#
# O simulador trabalha em uma CÓPIA do lab (.simulacao/), sem alterar os arquivos originais.
set -uo pipefail
export MSYS_NO_PATHCONV=1

variante=${1:-}
mudanca=${2:-}
if [ "$variante" != "antes" ] && [ "$variante" != "depois" ]; then
  sed -n '2,8p' "$0"; exit 1
fi

ORIGEM="$(cd "$(dirname "$0")/.." && pwd)"
TRAB="$ORIGEM/.simulacao"
rm -rf "$TRAB"; mkdir -p "$TRAB"
cp -r "$ORIGEM/app" "$ORIGEM/tests" "$ORIGEM/scripts" "$ORIGEM/requirements-dev.txt" "$ORIGEM/setup.cfg" "$ORIGEM/semgrep-regras.yml" "$TRAB/"
export RAIZ="$TRAB"
etapa() { bash "$TRAB/scripts/etapas.sh" "$@"; }

limpar() { for a in producao staging; do docker rm -f "tracking-$a" > /dev/null 2>&1; done; }
trap limpar EXIT
limpar

# --- Estado de partida: a versão 1.0.0 está em produção ---------------------------------------
echo "Preparando: versão 1.0.0 em produção (porta 8092)..."
VERSAO=1.0.0 etapa construir && VERSAO=1.0.0 etapa deploy producao 8092 && etapa smoke 8092 > /dev/null
echo

# --- A mudança do desenvolvedor ----------------------------------------------------------------
if [ -n "$mudanca" ]; then
  docker run --rm -v "$TRAB":/w -w /w python:3.12-slim python scripts/mudanca.py /w "$mudanca" || exit 1
else
  echo "Sem mudança ruim: um commit saudável."
fi
echo

T0=$(date +%s)
PRIMEIRO_AVISO=""

# rodar <rotulo> <ignorar 0|1> comando...
rodar() {
  local rotulo=$1 ignorar=$2; shift 2
  local ini fim saida rc estado
  ini=$(date +%s)
  saida=$("$@" 2>&1); rc=$?
  fim=$(date +%s)
  if [ $rc -eq 0 ]; then estado="ok"
  elif [ "$ignorar" = 1 ]; then estado="FALHOU (ignorado!)"
  else estado="FALHOU"; fi
  printf "[%4ss] %-38s %-20s (%ss)\n" $((fim - T0)) "$rotulo" "$estado" $((fim - ini))
  if [ $rc -ne 0 ] && [ -z "$PRIMEIRO_AVISO" ]; then PRIMEIRO_AVISO=$((fim - T0)); fi
  if [ $rc -ne 0 ] || [ -n "${MOSTRAR_SAIDA:-}" ]; then echo "$saida" | grep -v '^\s*$' | head -n 5 | sed 's/^/           | /'; fi
  [ "$ignorar" = 1 ] && return 0
  return $rc
}

verde() { echo; echo ">>> PIPELINE VERDE <<<"; }
vermelho() { echo; echo ">>> PIPELINE BARRADO: $1 <<<"; }

# ================================================================================================
if [ "$variante" = "antes" ]; then
  echo "== PIPELINE ANTES (com problemas) =="
  export VERSAO=latest                                              # problema: tag "latest", sem versão
  rodar "build da imagem (tag latest)" 0 etapa construir
  antes_publicar() {
    echo "login no registry com o token $TOKEN_REGISTRY"            # problema: segredo impresso no log
    etapa publicar
  }
  TOKEN_REGISTRY="token-de-exemplo-123456" MOSTRAR_SAIDA=1 rodar "publicar (antes de testar!)" 0 antes_publicar
  rodar "deploy direto em PRODUCAO" 0 etapa deploy producao 8090    # problema: sem staging, sem smoke
  rodar "testes (falha ignorada)" 1 etapa testes                    # problema: || true
  rodar "lint (falha ignorada)" 1 etapa lint
  verde
  echo
  if curl -fsS localhost:8090/saude > /dev/null 2>&1; then
    echo "O que está em produção agora: a aplicação responde."
  else
    echo "O que está em produção agora: a aplicação NÃO responde. O pipeline estava verde."
  fi
  [ -n "$PRIMEIRO_AVISO" ] && echo "O primeiro aviso de problema apareceu aos ${PRIMEIRO_AVISO}s, DEPOIS de a versão ir para produção, e foi ignorado."

# ================================================================================================
else
  echo "== PIPELINE DEPOIS (maduro) =="
  export VERSAO=1.1.0                                               # tag semântica, imutável
  # Qualidade e segurança: rápidas, primeiro. (No GitHub Actions rodam em paralelo.)
  rodar "lint" 0 etapa lint                                          || { vermelho "lint. Nada foi construído nem implantado."; exit 1; }
  rodar "testes + gate de cobertura (80%)" 0 etapa testes            || { vermelho "testes. Nada foi construído nem implantado."; exit 1; }
  rodar "segredos no código (gitleaks)" 0 etapa segredos             || { vermelho "segredo encontrado. Nada foi construído nem implantado."; exit 1; }
  rodar "SAST (semgrep)" 0 etapa sast                                || { vermelho "falha de segurança no código. Nada foi construído nem implantado."; exit 1; }
  rodar "SCA: dependências (trivy)" 0 etapa sca                      || { vermelho "dependência vulnerável. Nada foi construído nem implantado."; exit 1; }
  # Build e publicação: só chegam aqui versões que passaram em todos os gates.
  rodar "build da imagem (tag $VERSAO)" 0 etapa construir            || { vermelho "build."; exit 1; }
  rodar "scan da imagem (trivy, críticas)" 0 etapa scan_imagem       || { vermelho "imagem com vulnerabilidade crítica."; exit 1; }
  rodar "publicar ($VERSAO)" 0 etapa publicar
  # Implantação progressiva, com verificação e rollback.
  rodar "deploy em STAGING" 0 etapa deploy staging 8091
  rodar "smoke test em staging" 0 etapa smoke 8091                   || { vermelho "smoke em staging. Produção intocada."; exit 1; }
  echo "           (aprovação manual antes de produção: no GitHub, um 'environment' com revisor obrigatório)"
  rodar "deploy em PRODUCAO" 0 etapa deploy producao 8092
  if ! rodar "smoke test em produção" 0 etapa smoke 8092; then
    rodar "ROLLBACK automático para 1.0.0" 0 etapa deploy producao 8092 1.0.0
    rodar "smoke test após rollback" 0 etapa smoke 8092
    vermelho "falha em produção; rollback automático feito."
    exit 1
  fi
  verde
  echo "Em produção agora: versão $VERSAO, verificada por testes, análises de segurança e smoke tests."
fi
echo "Tempo total: $(( $(date +%s) - T0 ))s"
