#!/bin/sh
# Configuração do Vault para o lab: auditoria, chave mestra (transit), credenciais dinâmicas de banco,
# política mínima para a aplicação e um token para ela. Roda uma vez e termina.
set -eu

until vault status >/dev/null 2>&1; do sleep 1; done

# Idempotente: o Compose pode executar este contêiner de novo (por exemplo, ao rodar o 'lab').
if vault secrets list | grep -q '^transit/'; then
  echo "[ok] vault ja configurado"
  exit 0
fi

# 1. Auditoria: toda operação fica registrada (os valores sensíveis aparecem com hash).
vault audit enable file file_path=/vault/logs/audit.log >/dev/null
echo "[ok] auditoria habilitada"

# 2. Motor transit: cifra/decifra sem expor a chave. A KEK nunca sai do Vault.
vault secrets enable transit >/dev/null
vault write -f transit/keys/kek type=aes256-gcm96 >/dev/null
echo "[ok] chave mestra 'kek' criada no motor transit"

# 3. Motor de banco: gera usuários temporários do PostgreSQL sob demanda.
vault secrets enable database >/dev/null
vault write database/config/loja \
  plugin_name=postgresql-database-plugin \
  allowed_roles=app \
  connection_url="postgresql://{{username}}:{{password}}@postgres:5432/loja?sslmode=disable" \
  username=admin password=admin-lab >/dev/null
vault write database/roles/app \
  db_name=loja \
  creation_statements=@/vault-setup/role.sql \
  default_ttl=60s max_ttl=120s >/dev/null
echo "[ok] credenciais dinamicas de banco: papel 'app' (TTL 60 s, maximo 120 s)"

# 4. Política mínima da aplicação: cifrar, decifrar, rewrap e ler credenciais do papel 'app'. Nada de rotacionar chaves.
vault policy write app /vault-setup/app-policy.hcl >/dev/null
# (o Vault avisa, com código de saída 2, que um id de token personalizado é menos seguro: aceitável só no lab)
vault token create -id=app-lab-token -policy=app -ttl=24h >/dev/null 2>&1 || [ $? -eq 2 ]
echo "[ok] politica 'app' e token da aplicacao criados"
