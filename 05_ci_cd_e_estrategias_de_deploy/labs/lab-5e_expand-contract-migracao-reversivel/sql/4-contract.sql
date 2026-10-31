-- FASE 4: CONTRACT
-- Só execute depois que NENHUMA instância da v1 estiver em execução e a v2 estiver estável.
-- A partir daqui não há volta: a coluna antiga deixa de existir.
DROP TRIGGER trg_sincroniza_nome_cliente ON entregas;
DROP FUNCTION sincroniza_nome_cliente();
ALTER TABLE entregas DROP COLUMN nome_cliente;
ALTER TABLE entregas ALTER COLUMN destinatario_nome SET NOT NULL;
