-- Estado mantido pelo consumer ingênuo (sem nenhuma proteção).
CREATE TABLE ingenuo_entregas (
    entrega_id          text PRIMARY KEY,
    status              text NOT NULL,
    comissao_motorista  numeric(10, 2) NOT NULL DEFAULT 0
);

-- Estado mantido pelo consumer robusto. "seq" é a versão do evento já aplicada.
CREATE TABLE robusto_entregas (
    entrega_id          text PRIMARY KEY,
    status              text NOT NULL,
    seq                 int NOT NULL DEFAULT 0,
    comissao_motorista  numeric(10, 2) NOT NULL DEFAULT 0
);

-- Registro de eventos já processados, por grupo de consumers (chave de idempotência).
CREATE TABLE eventos_processados (
    grupo      text NOT NULL,
    event_id   text NOT NULL,
    PRIMARY KEY (grupo, event_id)
);

-- Notificações enviadas ao cliente pelo segundo consumer robusto.
CREATE TABLE notificacoes (
    event_id        text PRIMARY KEY,
    entrega_id      text NOT NULL,
    mensagem        text NOT NULL,
    correlation_id  text
);
