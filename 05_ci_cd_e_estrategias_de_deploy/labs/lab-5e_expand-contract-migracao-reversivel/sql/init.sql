-- Estado inicial: a tabela de entregas com a coluna antiga, nome_cliente.
CREATE TABLE entregas (
    id            serial PRIMARY KEY,
    nome_cliente  text NOT NULL,
    status        text NOT NULL DEFAULT 'criada'
);

INSERT INTO entregas (nome_cliente, status)
SELECT 'Cliente ' || n, 'em_rota' FROM generate_series(1, 5000) AS n;
