# A aplicação pode usar a chave 'kek' (cifrar, decifrar e rewrap), mas não pode rotacioná-la,
# exportá-la nem mudar a política. E pode ler credenciais de banco do papel 'app'.
path "transit/encrypt/kek" {
  capabilities = ["update"]
}
path "transit/decrypt/kek" {
  capabilities = ["update"]
}
path "transit/rewrap/kek" {
  capabilities = ["update"]
}
path "database/creds/app" {
  capabilities = ["read"]
}
