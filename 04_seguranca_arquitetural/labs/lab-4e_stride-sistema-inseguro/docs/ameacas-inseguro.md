# Ameacas deduzidas pelo pytm: inseguro

Total: **106** ameacas em 8 elementos do diagrama.

| Severidade | Quantidade |
|---|---|
| Very High | 10 |
| High | 35 |
| Medium | 53 |
| Low | 6 |
| Very Low | 2 |

## Por elemento

| Elemento | Ameacas |
|---|---|
| API de entregas | 45 |
| Servico de notificacao | 23 |
| Login e confirmacao de entrega | 8 |
| Consulta de entregas e relatorios | 7 |
| SQL | 7 |
| Le entregas concluidas e grava avisos | 7 |
| PostgreSQL | 5 |
| Aviso de entrega (SMS) | 4 |

## Ameacas mais severas

| Id | Elemento | Ameaca | Severidade |
|---|---|---|---|
| AC06 | API de entregas | Using Malicious Files | Very High |
| AC06 | Servico de notificacao | Using Malicious Files | Very High |
| AC17 | API de entregas | Session Hijacking - ServerSide | Very High |
| DS06 | Login e confirmacao de entrega | Data Leak | Very High |
| DS06 | Consulta de entregas e relatorios | Data Leak | Very High |
| DS06 | SQL | Data Leak | Very High |
| DS06 | Le entregas concluidas e grava avisos | Data Leak | Very High |
| HA01 | API de entregas | Path Traversal | Very High |
| INP05 | API de entregas | Command Line Execution through SQL Injection | Very High |
| SC02 | API de entregas | XSS Targeting Non-Script Elements | Very High |
| AA03 | API de entregas | Exploitation of Trusted Credentials | High |
| AA03 | Servico de notificacao | Exploitation of Trusted Credentials | High |
| AA04 | API de entregas | Exploiting Trust in Client | High |
| AA04 | Servico de notificacao | Exploiting Trust in Client | High |
| AC16 | API de entregas | Session Credential Falsification through Prediction | High |
