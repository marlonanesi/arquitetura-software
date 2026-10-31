-- O CAMINHO INGENUO: renomear a coluna de uma vez.
-- Tudo o que ainda usa nome_cliente (a v1 em execução) quebra no mesmo instante.
ALTER TABLE entregas RENAME COLUMN nome_cliente TO destinatario_nome;
