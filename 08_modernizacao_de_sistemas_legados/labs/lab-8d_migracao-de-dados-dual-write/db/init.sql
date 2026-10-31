-- Dois bancos: o do LEGADO (modelo antigo, com dados sujos) e o NOVO (modelo limpo).
CREATE DATABASE legado;
CREATE DATABASE novo;

\c legado
-- O modelo antigo: nomes crípticos, tudo como texto, formatos mistos.
CREATE TABLE entrega_tb (
    cod_ent text PRIMARY KEY,
    st      text NOT NULL,          -- "1", "2", "3", "9" (e alguns "7", inválidos)
    dt_prev text NOT NULL,          -- "dd/mm/aaaa", "aaaa-mm-dd" ou "N/D"
    vlr     text NOT NULL,          -- "123,40" ou "123.40"
    transp  text NOT NULL,          -- nome em maiúsculas com sufixo societário
    dt_alt  timestamptz NOT NULL DEFAULT now()    -- última alteração (permite copiar só o que mudou)
);
-- Fila de reparo: divergências conhecidas (uma escrita no banco novo que falhou durante o dual-write)
CREATE TABLE fila_reparo (id serial PRIMARY KEY, cod_ent text NOT NULL, motivo text NOT NULL, em timestamptz NOT NULL DEFAULT now());

-- 20.000 entregas. Cerca de 2% têm dado inválido de propósito (status inexistente ou data "N/D").
INSERT INTO entrega_tb (cod_ent, st, dt_prev, vlr, transp, dt_alt)
SELECT 'E-' || lpad(i::text, 6, '0'),
       CASE WHEN i % 97 = 0 THEN '7' WHEN i % 11 = 0 THEN '9' ELSE ((i % 3) + 1)::text END,
       CASE WHEN i % 89 = 0 THEN 'N/D'
            WHEN i % 5 = 0 THEN to_char(date '2026-11-01' + (i % 60), 'YYYY-MM-DD')
            ELSE to_char(date '2026-11-01' + (i % 60), 'DD/MM/YYYY') END,
       CASE WHEN i % 2 = 0 THEN replace((((i * 37) % 500000 + 1000) / 100.0)::numeric(12,2)::text, '.', ',')
            ELSE (((i * 37) % 500000 + 1000) / 100.0)::numeric(12,2)::text END,
       CASE i % 3 WHEN 0 THEN 'TRANSRAPIDA LTDA' WHEN 1 THEN 'VELOZ EXPRESS S/A' ELSE 'LOG BOREAL ME' END,
       now() - interval '30 days'
FROM generate_series(1, 20000) AS i;

\c novo
-- O modelo novo: limpo e tipado.
CREATE TABLE entregas (
    id                text PRIMARY KEY,
    status            text   NOT NULL,
    previsao          date   NOT NULL,
    valor_centavos    bigint NOT NULL,
    transportadora_id text   NOT NULL,
    origem            text   NOT NULL DEFAULT 'backfill',     -- backfill, dual-write, leitura, novo-primario
    atualizado_em     timestamptz NOT NULL DEFAULT now()
);
-- Dados que não puderam ser migrados: ficam à parte, com o motivo, para tratamento (não somem em silêncio).
CREATE TABLE quarentena (id text PRIMARY KEY, motivo text NOT NULL, bruto jsonb NOT NULL, em timestamptz NOT NULL DEFAULT now());
CREATE TABLE controle (chave text PRIMARY KEY, valor text NOT NULL);
