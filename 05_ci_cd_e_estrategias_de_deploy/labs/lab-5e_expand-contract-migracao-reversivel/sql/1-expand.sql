-- FASE 1: EXPAND
-- Só ADICIONA. Nada que a v1 usa muda, então a v1 continua funcionando sem perceber.
ALTER TABLE entregas ADD COLUMN destinatario_nome text;

-- Escrita dupla feita pelo próprio banco: enquanto as duas colunas existirem, uma
-- gravação em qualquer uma delas atualiza a outra. Assim a v1 e a v2 podem escrever
-- ao mesmo tempo e uma sempre enxerga o que a outra gravou.
CREATE FUNCTION sincroniza_nome_cliente() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.nome_cliente      := COALESCE(NEW.nome_cliente, NEW.destinatario_nome);
        NEW.destinatario_nome := COALESCE(NEW.destinatario_nome, NEW.nome_cliente);
    ELSIF NEW.nome_cliente IS DISTINCT FROM OLD.nome_cliente THEN
        NEW.destinatario_nome := NEW.nome_cliente;
    ELSIF NEW.destinatario_nome IS DISTINCT FROM OLD.destinatario_nome THEN
        NEW.nome_cliente := NEW.destinatario_nome;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sincroniza_nome_cliente
BEFORE INSERT OR UPDATE ON entregas
FOR EACH ROW EXECUTE FUNCTION sincroniza_nome_cliente();
