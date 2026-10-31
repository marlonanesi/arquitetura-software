-- O EVENT STORE: só se acrescenta (append-only). Nenhuma linha é atualizada nem apagada.
CREATE TABLE eventos (
    id           bigserial PRIMARY KEY,                -- ordem global
    agregado_id  text        NOT NULL,
    versao       int         NOT NULL,                 -- ordem dentro do agregado
    tipo         text        NOT NULL,
    esquema      int         NOT NULL DEFAULT 1,       -- versão do formato do evento
    dados        jsonb       NOT NULL,
    ator         text        NOT NULL,                 -- quem causou o fato (trilha de auditoria)
    ocorrido_em  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (agregado_id, versao)                       -- controle otimista de concorrência
);

-- Proteção de verdade: nem o dono da aplicação consegue alterar ou apagar um evento.
CREATE FUNCTION proibir_alteracao() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'o event store e imutavel: % nao e permitido', TG_OP; END $$;
CREATE TRIGGER eventos_imutaveis BEFORE UPDATE OR DELETE ON eventos FOR EACH ROW EXECUTE FUNCTION proibir_alteracao();

-- MODELOS DE LEITURA (projeções): derivados dos eventos, descartáveis e reconstruíveis.
CREATE TABLE proj_entregas (
    id text PRIMARY KEY, codigo text, status text, previsao text, transportadora text,
    reagendamentos int NOT NULL DEFAULT 0, versao int NOT NULL, atualizado_em timestamptz NOT NULL DEFAULT now());
CREATE TABLE proj_painel (
    transportadora text PRIMARY KEY, registradas int NOT NULL DEFAULT 0, em_rota int NOT NULL DEFAULT 0,
    entregues int NOT NULL DEFAULT 0, canceladas int NOT NULL DEFAULT 0, reagendamentos int NOT NULL DEFAULT 0);

CREATE TABLE projetor_controle (nome text PRIMARY KEY, valor bigint NOT NULL);
INSERT INTO projetor_controle VALUES ('ultimo_evento', 0), ('atraso_ms', 0);
