#!/usr/bin/env bash
# Mostra, linha a linha, o que mudou entre a versão insegura e a redesenhada (os marcadores [Fx] e [Cx] ligam falha e correção).
cd "$(dirname "$0")/.."
diff -u app/inseguro/main.py app/seguro/main.py | grep -E '^[+-]' | grep -v -E '^(\+\+\+|---)' | grep -E '\[[FC][0-9]\]'
