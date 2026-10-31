-- Tabela de tarifas de frete por rota (200 rotas).
CREATE TABLE tarifas (
    rota   text PRIMARY KEY,
    valor  numeric(10, 2) NOT NULL
);

INSERT INTO tarifas (rota, valor)
SELECT 'R' || lpad(n::text, 3, '0'), round((20 + random() * 180)::numeric, 2)
FROM generate_series(1, 200) AS n;
