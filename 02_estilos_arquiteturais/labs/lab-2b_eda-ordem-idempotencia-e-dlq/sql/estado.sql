\echo '=== Estado das entregas: consumer ingenuo x consumer robusto ==='
SELECT COALESCE(i.entrega_id, r.entrega_id) AS entrega,
       i.status                AS status_ingenuo,
       i.comissao_motorista    AS comissao_ingenuo,
       r.status                AS status_robusto,
       r.comissao_motorista    AS comissao_robusto
FROM ingenuo_entregas i
FULL JOIN robusto_entregas r ON r.entrega_id = i.entrega_id
ORDER BY 1;

\echo '=== Notificacoes enviadas ao cliente (consumer robusto-notificacao) ==='
SELECT entrega_id, mensagem, correlation_id FROM notificacoes ORDER BY entrega_id, event_id;
