-- FASE 2: BACKFILL
-- Copia os dados antigos para a coluna nova. Em produção, faça em lotes pequenos, com
-- commit entre eles, para não segurar locks por muito tempo. Aqui são 5 mil linhas,
-- então um laço simples basta; o princípio é o mesmo.
DO $$
DECLARE
    afetadas int;
BEGIN
    LOOP
        UPDATE entregas
           SET destinatario_nome = nome_cliente
         WHERE id IN (SELECT id FROM entregas WHERE destinatario_nome IS NULL LIMIT 1000);
        GET DIAGNOSTICS afetadas = ROW_COUNT;
        EXIT WHEN afetadas = 0;
    END LOOP;
END $$;
