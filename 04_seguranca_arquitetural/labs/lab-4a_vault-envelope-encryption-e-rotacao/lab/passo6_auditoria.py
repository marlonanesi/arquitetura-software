"""Passo 6: o log de auditoria do Vault. Quem fez o quê, quando e com sucesso ou não (valores com hash)."""
import json
import sys

N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
linhas = open("/vault/logs/audit.log", encoding="utf-8").read().splitlines()
registros = []
for linha in linhas:
    e = json.loads(linha)
    if e.get("type") != "response":
        continue
    req, resp = e.get("request", {}), e.get("response", {})
    caminho = req.get("path", "")
    if not caminho.startswith(("transit/", "database/creds", "sys/leases", "auth/token")):
        continue
    registros.append((e["time"][11:19], req.get("operation"), caminho,
                      " ".join((e.get("error") or "ok").split()), (e.get("auth") or {}).get("display_name") or "-",
                      ",".join((e.get("auth") or {}).get("policies") or [])))

print(f"{'hora':<9} {'operacao':<9} {'caminho':<28} {'resultado':<30} {'token':<14} politicas")
for hora, op, caminho, resultado, token, politicas in registros[-N:]:
    print(f"{hora:<9} {op:<9} {caminho:<28} {resultado[:28]:<30} {token:<14} {politicas}")
print("\nExemplo de uma entrada completa (note os valores sensiveis com hash, nunca em claro):")
unicas = [json.loads(l) for l in linhas if ('"transit/encrypt/kek"' in l or '"transit/decrypt/kek"' in l) and "batch_input" not in l]
ultima = unicas[-1]
print(json.dumps({"request.path": ultima["request"]["path"], "request.data": ultima["request"].get("data"),
                  "auth.policies": (ultima.get("auth") or {}).get("policies")}, indent=2, ensure_ascii=False)[:600])
