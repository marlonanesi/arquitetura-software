#!/usr/bin/env bash
# Imprime uma "impressão digital" do pacote de domínio. Se ela não muda depois de trocar ou adicionar
# um adaptador, o domínio não foi tocado.
cd "$(dirname "$0")/../src/confirmacao/dominio" || exit 1
echo "dominio: $(cat *.py | sha256sum | cut -c1-16)  ($(ls *.py | wc -l) arquivos)"
