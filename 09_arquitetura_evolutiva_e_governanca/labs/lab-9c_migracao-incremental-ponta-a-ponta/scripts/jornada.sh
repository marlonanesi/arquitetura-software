#!/usr/bin/env bash
# A jornada inteira, de ponta a ponta, em cerca de 4 minutos: do legado puro até o legado desligado,
# passando por backfill, dual-write, sombra, canário, uma falha injetada com rollback automático e a virada.
# Pensada para a aula: cada etapa imprime o que vai fazer e o painel de marcos no fim.
set -u
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1
F="docker compose --profile ferramentas run --rm -T ferramentas python"
quieto() { grep -v '^ Container'; }
titulo() { echo; echo "=================== $1"; }
zerar() { curl -s -X POST localhost:9501/admin/zerar >/dev/null; }
falha_novo() { docker compose exec -T novo python -c "import urllib.request; urllib.request.urlopen(urllib.request.Request('http://localhost:8000/admin/falha?pct=$1', method='POST'))"; }

titulo "0. Ponto de partida: tudo no legado"
$F flags.py mostrar | quieto; $F progresso.py | quieto | head -3

titulo "1. Backfill: copiar o histórico para o banco novo"
$F dados.py backfill | quieto; $F dados.py verificar | quieto

titulo "2. Modo sombra ligado, mas a escrita ainda só no legado: o novo envelhece e a sombra acusa"
$F flags.py sombra on | quieto; zerar; $F carga.py 12 40 | quieto
curl -s localhost:9501/metricas | python -c "import sys,json; m=json.load(sys.stdin); print('sombra: iguais =', m['sombra_iguais'], '| divergentes =', m['sombra_divergentes'])"

titulo "3. Dual-write ligado e reconciliação do que ficou para trás"
$F flags.py escrita dupla | quieto; $F dados.py reconciliar | quieto; $F dados.py verificar | quieto

titulo "4. Sombra de novo, agora sem divergência"
zerar; $F carga.py 15 40 | quieto
curl -s localhost:9501/metricas | python -c "import sys,json; m=json.load(sys.stdin); print('sombra: iguais =', m['sombra_iguais'], '| divergentes =', m['sombra_divergentes'])"

titulo "5. Canário: 5% e depois 25% dos usuários leem do novo"
zerar; $F flags.py leitura 5 | quieto; sleep 2; $F carga.py 12 40 | quieto
$F flags.py leitura 25 | quieto; sleep 2; $F carga.py 12 40 | quieto
$F progresso.py | quieto | grep -E "^M[1-4]"

titulo "6. GAME DAY: o novo começa a falhar em 50% das chamadas; o guardião liga o rollback sozinho"
docker compose up -d guardiao 2>&1 | quieto | tail -1; sleep 3; zerar; falha_novo 50
$F carga.py 25 40 | quieto
docker compose logs guardiao 2>&1 | grep ROLLBACK | tail -1
curl -s localhost:9501/metricas | python -c "import sys,json; m=json.load(sys.stdin); print('erros do novo =', m['erros_novo'], '| fallbacks para o legado =', m['fallbacks'], '| kill switch =', m['flags']['kill_switch_novo'])"

titulo "7. O novo se recupera: reconcilia o que a falha deixou, desliga o kill switch e retoma"
falha_novo 0; $F dados.py reconciliar | quieto; $F flags.py kill off | quieto; $F flags.py sombra off | quieto
zerar; $F flags.py leitura 50 | quieto; $F carga.py 12 40 | quieto

titulo "8. A virada: leitura 100% e escrita no novo (o legado recebe uma cópia, para o rollback)"
zerar; $F flags.py leitura 100 | quieto; $F flags.py escrita novo | quieto; $F carga.py 15 40 | quieto; $F dados.py verificar | quieto
echo "(a cópia para o legado é feita depois da escrita no novo; duas escritas concorrentes no mesmo registro podem inverter a ordem lá)"
$F dados.py reconciliar-legado | quieto; $F dados.py verificar | quieto

titulo "9. Desligar o legado e seguir operando"
docker compose stop legado 2>&1 | quieto | tail -1; $F carga.py 8 40 | quieto

titulo "10. O painel de marcos"
$F progresso.py | quieto
