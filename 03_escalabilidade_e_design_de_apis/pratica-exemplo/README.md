# Aula 3.11 — Analisando contratos de API: do bom ao problemático

Aplicação FastAPI para explorar antipadrões e boas práticas de design de APIs REST.

## Como rodar

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Abra o Swagger em **http://127.0.0.1:8000/docs**

## O que explorar

Os endpoints estão organizados em 5 temas, cada um com um par **Ruim / Certo**:

| # | Tema |
|---|---|
| 1 | Verbos HTTP e nomes de recursos |
| 2 | Status codes |
| 3 | Paginação |
| 4 | Idempotência |
| 5 | Versionamento |

> **Atenção:** Os endpoints marcados com `🔴 ERRADO` têm **50% de chance** de retornar HTTP `200` com erro no corpo. Chame algumas vezes e observe o comportamento.

## Dica: testando idempotência

1. Chame `POST /v1/confirmacoes` com o header `Idempotency-Key: qualquer-valor-fixo`
2. Chame novamente com o **mesmo** header
3. Compare o `confirmacao_id` nas duas respostas — deve ser idêntico

## Dica: testando status codes corretos

No `DELETE /v1/envios/{envio_id}`, use estes IDs especiais:

| ID | Resultado esperado |
|---|---|
| `NOTFOUND` | 404 Not Found |
| `EMTRANSITO` | 409 Conflict |
| qualquer outro | 204 No Content |
