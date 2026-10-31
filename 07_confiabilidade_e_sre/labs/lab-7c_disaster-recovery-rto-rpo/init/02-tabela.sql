CREATE TABLE entregas (
    id         bigserial PRIMARY KEY,
    status     text NOT NULL,
    criada_em  timestamptz NOT NULL DEFAULT now()
);
