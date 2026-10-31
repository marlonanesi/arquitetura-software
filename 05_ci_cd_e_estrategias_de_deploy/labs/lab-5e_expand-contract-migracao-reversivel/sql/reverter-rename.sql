-- Desfaz o rename direto, para voltar ao estado inicial e seguir com o expand-contract.
ALTER TABLE entregas RENAME COLUMN destinatario_nome TO nome_cliente;
