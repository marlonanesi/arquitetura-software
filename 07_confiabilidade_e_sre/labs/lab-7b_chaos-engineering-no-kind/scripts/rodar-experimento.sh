#!/usr/bin/env bash
# Roda UM experimento de caos do começo ao fim, com as quatro etapas do método:
#   1. confirma o estado estacionário (o sistema está saudável ANTES do ataque)
#   2. inicia o tráfego de medição
#   3. injeta a falha (arquivo de experimentos/)
#   4. lê o resultado e remove o experimento (a condição de abortar também remove)
#
# Uso: scripts/rodar-experimento.sh experimentos/e1-pod-kill.yaml [ABORTAR]
#   ABORTAR=sim liga a condição de abortar no k6 (o teste para se o alvo protegido violar a hipótese).
set -u
cd "$(dirname "$0")/.."

EXP="${1:?informe o arquivo do experimento, ex.: experimentos/e1-pod-kill.yaml}"
ABORTAR="${2:-nao}"
NS=caos
ATRASO_ATAQUE=15   # segundos de tráfego normal antes de injetar a falha

echo "== 1. Estado estacionário"
for alvo in frete-fragil frete-protegido; do
  kubectl -n $NS rollout status deploy/$alvo --timeout=120s >/dev/null || { echo "$alvo nao esta pronto"; exit 1; }
done
kubectl -n $NS rollout status deploy/transportadora --timeout=120s >/dev/null
kubectl -n $NS get pods
kubectl -n $NS create configmap k6-scripts --from-file=k6/ --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "== 2. Tráfego de medição"
kubectl -n $NS delete job experimento --ignore-not-found >/dev/null
sed "s/value: \"nao\"/value: \"$ABORTAR\"/" manifests/40-job-experimento.yaml | kubectl apply -f - >/dev/null
sleep "$ATRASO_ATAQUE"

echo "== 3. Injetando a falha: $EXP"
kubectl apply -f "$EXP"

echo "== 4. Aguardando o fim da medição"
for i in $(seq 1 120); do
  FASE=$(kubectl -n $NS get job experimento -o jsonpath='{.status.succeeded}{.status.failed}' 2>/dev/null)
  [ -n "$FASE" ] && break
  sleep 3
done
kubectl delete -f "$EXP" --ignore-not-found >/dev/null
echo
kubectl -n $NS logs job/experimento | grep -A3 -E "RESULTADO DO EXPERIMENTO|level=error|aborted" | head -n 20
