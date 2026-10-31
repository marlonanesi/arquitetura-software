-- Dois bancos no mesmo PostgreSQL: um para cada variante, com o mesmo esquema.
CREATE DATABASE modular;
CREATE DATABASE distribuido;

\c modular
CREATE TABLE entregas (id serial PRIMARY KEY, codigo text NOT NULL, destino text NOT NULL, status text NOT NULL, criada_em timestamptz NOT NULL DEFAULT now());
CREATE TABLE rotas (id serial PRIMARY KEY, entrega_id int NOT NULL, sequencia int NOT NULL, motorista text NOT NULL);
CREATE TABLE notificacoes (id serial PRIMARY KEY, entrega_id int NOT NULL, canal text NOT NULL, enviada_em timestamptz NOT NULL DEFAULT now());

\c distribuido
CREATE TABLE entregas (id serial PRIMARY KEY, codigo text NOT NULL, destino text NOT NULL, status text NOT NULL, criada_em timestamptz NOT NULL DEFAULT now());
CREATE TABLE rotas (id serial PRIMARY KEY, entrega_id int NOT NULL, sequencia int NOT NULL, motorista text NOT NULL);
CREATE TABLE notificacoes (id serial PRIMARY KEY, entrega_id int NOT NULL, canal text NOT NULL, enviada_em timestamptz NOT NULL DEFAULT now());
