-- Dois bancos: o do LEGADO (modelo antigo, 2.000 entregas) e o NOVO (modelo limpo e vazio).
CREATE DATABASE legado;
CREATE DATABASE novo;

\c legado
CREATE TABLE entrega_tb (
    cod_ent text PRIMARY KEY, st text NOT NULL, dt_prev text NOT NULL, vlr text NOT NULL, transp text NOT NULL,
    dt_alt timestamptz NOT NULL DEFAULT now());
CREATE TABLE fila_reparo (id serial PRIMARY KEY, cod_ent text NOT NULL, motivo text NOT NULL, em timestamptz NOT NULL DEFAULT now());
INSERT INTO entrega_tb (cod_ent, st, dt_prev, vlr, transp)
SELECT 'E-' || lpad(i::text, 6, '0'),
       ((i % 3) + 1)::text,
       CASE WHEN i % 5 = 0 THEN to_char(date '2026-11-01' + (i % 60), 'YYYY-MM-DD') ELSE to_char(date '2026-11-01' + (i % 60), 'DD/MM/YYYY') END,
       CASE WHEN i % 2 = 0 THEN replace((((i * 37) % 500000 + 1000) / 100.0)::numeric(12,2)::text, '.', ',')
            ELSE (((i * 37) % 500000 + 1000) / 100.0)::numeric(12,2)::text END,
       CASE i % 3 WHEN 0 THEN 'TRANSRAPIDA LTDA' WHEN 1 THEN 'VELOZ EXPRESS S/A' ELSE 'LOG BOREAL ME' END
FROM generate_series(1, 2000) AS i;

\c novo
CREATE TABLE entregas (
    id text PRIMARY KEY, status text NOT NULL, previsao date NOT NULL, valor_centavos bigint NOT NULL,
    transportadora_id text NOT NULL, origem text NOT NULL DEFAULT 'backfill', atualizado_em timestamptz NOT NULL DEFAULT now());
