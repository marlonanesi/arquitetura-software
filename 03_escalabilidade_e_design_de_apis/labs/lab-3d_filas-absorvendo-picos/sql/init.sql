CREATE TABLE confirmacoes (
    id            serial PRIMARY KEY,
    codigo        text NOT NULL UNIQUE,
    recebida_em   timestamptz NOT NULL,
    processada_em timestamptz NOT NULL
);
