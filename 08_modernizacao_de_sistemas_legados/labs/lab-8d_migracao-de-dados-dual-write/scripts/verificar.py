"""Verificação de consistência entre o legado e o novo: contagem e checksum por faixa de 1.000 ids.

  python verificar.py            resumo
  python verificar.py --detalhe  lista as linhas divergentes

Compara as entregas do legado JÁ TRADUZIDAS com as do banco novo, na forma canônica. Os registros que a
tradução rejeita (quarentena) ficam de fora, e são contados à parte. Sai com código 1 se houver divergência,
para poder ser usada como uma verificação de CI ou de plantão.
"""
import hashlib
import sys
from collections import defaultdict

import comum
import traducao

detalhe = "--detalhe" in sys.argv

with comum.legado() as cl, comum.novo() as cn:
    validas, invalidas = comum.ler_legado_traduzido(cl)
    no_novo = comum.ler_novo(cn)
    em_quarentena = cn.execute("SELECT count(*) FROM quarentena").fetchone()[0]


def checksums(entregas: dict) -> dict:
    por_faixa = defaultdict(list)
    for cod in sorted(entregas):
        por_faixa[comum.bucket(cod)].append(traducao.forma_canonica(entregas[cod]))
    return {f: (len(l), hashlib.md5("\n".join(l).encode()).hexdigest()[:10]) for f, l in por_faixa.items()}


a, b = checksums(validas), checksums(no_novo)
faixas_ruins = sorted(f for f in set(a) | set(b) if a.get(f) != b.get(f))

faltando = sorted(set(validas) - set(no_novo))
sobrando = sorted(set(no_novo) - set(validas))
diferentes = sorted(c for c in set(validas) & set(no_novo) if traducao.forma_canonica(validas[c]) != traducao.forma_canonica(no_novo[c]))

print(f"legado: {len(validas) + len(invalidas)} registros ({len(validas)} traduziveis, {len(invalidas)} invalidos)")
print(f"novo:   {len(no_novo)} entregas, {em_quarentena} na quarentena")
print(f"faixas de 1.000 ids: {len(set(a) | set(b))}, divergentes: {len(faixas_ruins)}")
print(f"linhas: faltando no novo={len(faltando)}  diferentes={len(diferentes)}  a mais no novo={len(sobrando)}")
if detalhe:
    for c in faltando[:10]:
        print(f"  falta no novo: {c}")
    for c in diferentes[:10]:
        print(f"  diferente: legado={traducao.forma_canonica(validas[c])}  novo={traducao.forma_canonica(no_novo[c])}")
    for c in sobrando[:10]:
        print(f"  a mais no novo: {c}")
ok = not (faltando or diferentes or sobrando)
print("RESULTADO: " + ("CONSISTENTE" if ok else "DIVERGENTE"))
sys.exit(0 if ok else 1)
