#!/usr/bin/env bash
# Verificações de arquitetura como código: modelo C4, ADRs e diagramas.
# É o que o CI roda em cada pull request. Precisa de Docker e Python 3.
set -eu
cd "$(dirname "$0")/.."
export MSYS_NO_PATHCONV=1   # Git Bash no Windows não deve reescrever os caminhos do container
export PYTHONUTF8=1         # acentos corretos na saída do validador de ADRs no Windows

MONTAGEM="$(pwd -W 2>/dev/null || pwd):/usr/local/structurizr"
STRUCTURIZR="docker run --rm -v $MONTAGEM structurizr/structurizr"

echo "== 1. Sintaxe do modelo (validate)"
$STRUCTURIZR validate -w workspace.dsl

echo "== 2. Qualidade do modelo (inspect): relacionamentos sem tecnologia, falta de documentação"
if $STRUCTURIZR inspect -w workspace.dsl | grep -E "^(ERROR|WARNING)"; then
  echo "O modelo tem pendências (acima)."; exit 1
fi
echo "sem pendências"

echo "== 3. ADRs (formato, status e substituições)"
PY=""
for c in python3 python; do
  if "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
done
[ -n "$PY" ] || { echo "Python 3 nao encontrado"; exit 1; }
$PY scripts/verificar_adrs.py adrs

echo "== 4. Diagramas gerados a partir do modelo (Mermaid)"
$STRUCTURIZR export -w workspace.dsl -f mermaid -o diagramas | grep Writing | sed 's|.*/diagramas/|  diagramas/|'

# Cada diagrama também vira uma página Markdown, que o GitHub renderiza (e que aparece no diff do PR).
for mmd in diagramas/*.mmd; do
  nome="$(basename "$mmd" .mmd)"; nome="${nome#structurizr-}"
  { echo "# Diagrama: $nome"; echo; echo "> Gerado a partir de workspace.dsl. Não edite à mão."; echo; echo '```mermaid'; cat "$mmd"; echo '```'; } > "diagramas/$nome.md"
done
rm -f diagramas/*.mmd
echo "  diagramas/*.md (renderizáveis no GitHub)"
