-- Antes de qualquer passo irreversível: as duas colunas estão consistentes?
SELECT count(*)                                                 AS total,
       count(*) FILTER (WHERE destinatario_nome IS NULL)        AS nova_coluna_vazia,
       count(*) FILTER (WHERE destinatario_nome IS DISTINCT FROM nome_cliente) AS divergentes
FROM entregas;
