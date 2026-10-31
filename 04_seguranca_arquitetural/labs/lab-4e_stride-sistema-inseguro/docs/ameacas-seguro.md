# Ameacas deduzidas pelo pytm: seguro

Total: **51** ameacas em 8 elementos do diagrama.

| Severidade | Quantidade |
|---|---|
| Very High | 4 |
| High | 16 |
| Medium | 26 |
| Low | 5 |

## Por elemento

| Elemento | Ameacas |
|---|---|
| API de entregas | 12 |
| Servico de notificacao | 11 |
| Consulta de entregas e relatorios | 6 |
| SQL | 6 |
| Le entregas concluidas e grava avisos | 6 |
| Login e confirmacao de entrega | 4 |
| Aviso de entrega (SMS) | 4 |
| PostgreSQL | 2 |

## Ameacas mais severas

| Id | Elemento | Ameaca | Severidade |
|---|---|---|---|
| DS06 | Login e confirmacao de entrega | Data Leak | Very High |
| DS06 | Consulta de entregas e relatorios | Data Leak | Very High |
| DS06 | SQL | Data Leak | Very High |
| DS06 | Le entregas concluidas e grava avisos | Data Leak | Very High |
| AC22 | Login e confirmacao de entrega | Credentials Aging | High |
| CR06 | Login e confirmacao de entrega | Communication Channel Manipulation | High |
| CR06 | Consulta de entregas e relatorios | Communication Channel Manipulation | High |
| CR06 | SQL | Communication Channel Manipulation | High |
| CR06 | Le entregas concluidas e grava avisos | Communication Channel Manipulation | High |
| CR06 | Aviso de entrega (SMS) | Communication Channel Manipulation | High |
| DR01 | Consulta de entregas e relatorios | Unprotected Sensitive Data | High |
| DR01 | SQL | Unprotected Sensitive Data | High |
| DR01 | Le entregas concluidas e grava avisos | Unprotected Sensitive Data | High |
| INP04 | API de entregas | HTTP Request Splitting | High |
| INP22 | API de entregas | XML Attribute Blowup | High |
