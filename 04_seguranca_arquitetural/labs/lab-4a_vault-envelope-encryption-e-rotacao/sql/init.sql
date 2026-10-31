-- Registros sensíveis da LunaLog: o dado fica cifrado; a chave de dados (DEK) fica cifrada pela chave mestra (KEK) no Vault.
CREATE TABLE registros (
    id          serial PRIMARY KEY,
    codigo      text NOT NULL UNIQUE,
    dado        bytea NOT NULL,        -- dado cifrado com a DEK (AES-256-GCM)
    nonce       bytea NOT NULL,
    dek_cifrada text  NOT NULL         -- a DEK cifrada pelo Vault ("vault:v1:...")
);
