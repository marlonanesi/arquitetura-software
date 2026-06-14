"""
LunaLog API — Design Bom vs. Ruim
Aula 3.11 | Analisando contratos de API: do bom ao problemático

Execute com:
    uvicorn main:app --reload

Acesse o Swagger em:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Header, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import random
import uuid
from datetime import datetime, timedelta


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="🚚 LunaLog API — Bom vs. Ruim",
    description="""
## Aula 3.11 | Analisando contratos de API: do bom ao problemático

Esta aplicação demonstra **os erros mais comuns em design de APIs REST** e
os padrões corretos correspondentes, usando como domínio a plataforma LunaLog
de logística e rastreamento de cargas.

---

### Como navegar esta demo

| Prefixo | O que é |
|---|---|
| `/bad/` | Antipadrões reais encontrados no mercado |
| `/v1/` e `/v2/` | Design correto, pronto para produção |

> **Atenção:** Os endpoints `/bad/` têm **50% de chance** de retornar HTTP `200`
> com erro no corpo — o antipadrão mais perigoso e comum em sistemas legados.

---

### Seções desta demo (ordem de apresentação)

1. **Verbos HTTP e Nomes de Recursos** — 3.1 / 3.6
2. **Status Codes** — 3.6
3. **Paginação** — 3.4 / 3.6
4. **Idempotência** — 3.6 / 3.8
5. **Versionamento** — 3.6
""",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "🔴 1 | Verbos e Nomes",
            "description": (
                "**Antipadrões:** verbo no path, GET que muta estado, POST para leitura. "
                "Cada endpoint tem **50% de chance** de retornar `200` com erro no corpo."
            ),
        },
        {
            "name": "🟢 1 | Verbos e Nomes",
            "description": "Substantivos no plural, verbos HTTP corretos, hierarquia de recursos clara.",
        },
        {
            "name": "🔴 2 | Status Codes",
            "description": (
                "**Antipadrões:** `200` para erros, `200` para criação, `200` para deleção de recurso inexistente. "
                "**50% de chance** de retornar `200` com erro no corpo."
            ),
        },
        {
            "name": "🟢 2 | Status Codes",
            "description": "`201 Created`, `204 No Content`, `404 Not Found`, `409 Conflict` — cada código com semântica precisa.",
        },
        {
            "name": "🔴 3 | Paginação",
            "description": (
                "**Antipadrões:** retorna todos os registros, paginação por offset em tabela grande. "
                "**50% de chance** de retornar `200` com erro no corpo."
            ),
        },
        {
            "name": "🟢 3 | Paginação",
            "description": "Paginação por cursor com metadata completo — performance constante em qualquer volume.",
        },
        {
            "name": "🔴 4 | Idempotência",
            "description": (
                "**Antipadrão:** POST sem proteção contra duplicatas — retry de rede gera confirmações duplas. "
                "**50% de chance** de retornar `200` com erro no corpo."
            ),
        },
        {
            "name": "🟢 4 | Idempotência",
            "description": "Header `Idempotency-Key` garante que retries retornam o mesmo resultado sem duplicar dados.",
        },
        {
            "name": "🔴 5 | Versionamento",
            "description": (
                "**Antipadrão:** API sem versão — qualquer mudança de contrato quebra todos os clientes integrados. "
                "**50% de chance** de retornar `200` com erro no corpo."
            ),
        },
        {
            "name": "🟢 5 | Versionamento",
            "description": "Versão na URL, headers `Deprecation`/`Sunset`, v1 e v2 coexistindo sem breaking change.",
        },
    ],
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers & mocks
# ─────────────────────────────────────────────────────────────────────────────

def coin_flip() -> bool:
    """Retorna True 50% das vezes — simula o antipadrão de erro no corpo com status 200."""
    return random.random() < 0.5


def _envio(id: str = None) -> dict:
    eid = id or str(uuid.uuid4())[:8].upper()
    return {
        "id": eid,
        "origem": "São Paulo, SP",
        "destino": "Rio de Janeiro, RJ",
        "peso_kg": round(random.uniform(0.5, 120.0), 2),
        "status": random.choice(["aguardando_coleta", "em_transito", "entregue"]),
        "criado_em": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
    }


def _eventos(envio_id: str) -> list:
    return [
        {"status": "coletado",          "local": "São Paulo, SP",     "data": (datetime.now() - timedelta(hours=48)).isoformat()},
        {"status": "em_transito",       "local": "Campinas, SP",      "data": (datetime.now() - timedelta(hours=24)).isoformat()},
        {"status": "saiu_para_entrega", "local": "Rio de Janeiro, RJ","data": (datetime.now() - timedelta(hours=2)).isoformat()},
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Modelos
# ─────────────────────────────────────────────────────────────────────────────

class EnvioCreate(BaseModel):
    origem: str  = Field(..., example="São Paulo, SP")
    destino: str = Field(..., example="Rio de Janeiro, RJ")
    peso_kg: float = Field(..., gt=0, example=12.5)
    descricao: str = Field(..., example="Eletrônicos frágeis — manusear com cuidado")


class EnvioPartialUpdate(BaseModel):
    destino:  Optional[str] = Field(None, example="Curitiba, PR")
    descricao: Optional[str] = Field(None, example="Nova descrição da carga")


class EnderecoUpdate(BaseModel):
    rua:         str = Field(..., example="Av. Paulista")
    numero:      str = Field(..., example="1000")
    cidade:      str = Field(..., example="São Paulo")
    cep:         str = Field(..., example="01310-100")
    complemento: Optional[str] = Field(None, example="Sala 42")


# Loja em memória para simular idempotência
_idempotency_store: dict = {}


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — VERBOS HTTP E NOMES DE RECURSOS
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/bad/getListagemDeEnvios",
    tags=["🔴 1 | Verbos e Nomes"],
    summary="❌ Verbo 'get' no path + retorna tudo sem paginação",
    description="""
**Problemas acumulados neste endpoint:**

- `getListagem` — verbo no path é redundante; o método HTTP **já é** `GET`
- Retorna todos os registros sem paginação — em produção com 500 k linhas: timeout e banco no limite
- Nome no singular misturado com ação verbal — não segue a convenção REST de substantivo no plural
- Estrutura de resposta mistura metadados de debug com dados reais

**→ 50% de chance de retornar `200` com erro no corpo.** Recarregue algumas vezes.
""",
)
def bad_get_listagem_de_envios():
    if coin_flip():
        return {
            "status": "error",
            "message": "Erro interno ao buscar envios. Contate o suporte.",
            "data": None,
        }
    # Simula dump de tabela inteira — 200 registros aqui, 500k em produção
    return {
        "getEnvios": [_envio(str(i)) for i in range(1, 201)],
        "timestamp": datetime.now().isoformat(),
        "debug_info": "full table scan executed",
    }


@app.get(
    "/bad/processarEntregaDoEnvio/{envio_id}",
    tags=["🔴 1 | Verbos e Nomes"],
    summary="❌ GET que modifica estado (side effect em método seguro)",
    description="""
**Problema central: GET nunca deve mutar estado.**

- O HTTP define GET como *safe* e *idempotent* — proxies e caches vão repetir este request
- Um health check ou crawler chamando esse endpoint **confirma entregas reais**
- CDNs, reverse proxies e navegadores fazem prefetch de links GET — efeito colateral invisível
- Testes de carga vão mutar o banco de produção sem querer

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_get_processar_entrega(envio_id: str):
    if coin_flip():
        return {"status": "error", "message": "Falha ao processar entrega", "data": None}
    # Muta estado via GET — antipadrão crítico
    return {
        "message": f"Entrega {envio_id} processada e marcada como entregue",
        "novo_status": "entregue",
        "processado_em": datetime.now().isoformat(),
        "aviso": "isso foi feito por um GET — qualquer cache pode repetir",
    }


@app.post(
    "/bad/buscarDetalheEnvio/{envio_id}",
    tags=["🔴 1 | Verbos e Nomes"],
    summary="❌ POST para operação de leitura",
    description="""
**Problema: POST para buscar dados.**

- POST não é idempotente — clientes não podem fazer retry seguro
- Resposta não pode ser cacheada por CDN ou cliente HTTP
- Quebra a semântica REST: POST **cria** recursos, não **lê**
- Ferramentas de monitoramento, APM e log trackers ficam confusos

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_post_buscar_envio(envio_id: str):
    if coin_flip():
        return {"status": "error", "message": "Envio não encontrado", "data": None}
    return _envio(envio_id)


# ── CORRETOS ──────────────────────────────────────────────────────────────────

@app.get(
    "/v1/envios",
    tags=["🟢 1 | Verbos e Nomes"],
    summary="✅ Listagem correta: substantivo plural, paginada, filtrável",
    description="""
**Por que está certo:**

- `/envios` — substantivo no plural, sem verbo
- Paginação obrigatória com `page` + `limit`, defaults razoáveis
- Filtro por `status` via query param — sem over-fetching
- Metadata de paginação no envelope de resposta
""",
)
def good_list_envios(
    page:   int = Query(1,  ge=1,                   description="Número da página (começa em 1)"),
    limit:  int = Query(20, ge=1, le=100,            description="Itens por página (máx 100)"),
    status: Optional[str] = Query(None,              description="Filtrar por status do envio"),
):
    envios = [_envio(str((page - 1) * limit + i)) for i in range(1, limit + 1)]
    total = 843
    total_pages = (total + limit - 1) // limit
    return {
        "data": envios,
        "pagination": {
            "page":        page,
            "limit":       limit,
            "total":       total,
            "total_pages": total_pages,
            "has_next":    page < total_pages,
            "has_prev":    page > 1,
        },
    }


@app.get(
    "/v1/envios/{envio_id}",
    tags=["🟢 1 | Verbos e Nomes"],
    summary="✅ GET por ID: seguro, idempotente, cacheável",
    description="""
**Por que está certo:**

- GET puro — sem side effects, pode ser repetido à vontade
- Retorna `404` se não encontrado (use `id = NOTFOUND` para testar)
- Resposta cacheável por CDN
""",
)
def good_get_envio(envio_id: str):
    if envio_id.upper() == "NOTFOUND":
        raise HTTPException(
            status_code=404,
            detail={"error": "envio_not_found", "message": f"Envio '{envio_id}' não existe"},
        )
    return _envio(envio_id)


@app.post(
    "/v1/envios/{envio_id}/entregas",
    tags=["🟢 1 | Verbos e Nomes"],
    status_code=201,
    summary="✅ POST para criar evento de entrega (sub-recurso)",
    description="""
**Por que está certo:**

- POST **cria** um novo evento de entrega — semântica correta
- Retorna `201 Created` com o recurso criado
- Path hierárquico: `/envios/{id}/entregas` — relação pai-filho explícita
""",
)
def good_post_entrega(envio_id: str):
    return JSONResponse(
        status_code=201,
        content={
            "id":             str(uuid.uuid4()),
            "envio_id":       envio_id,
            "status":         "entregue",
            "registrado_em":  datetime.now().isoformat(),
            "entregue_por":   "Motorista João Silva",
        },
    )


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — STATUS CODES
# ═════════════════════════════════════════════════════════════════════════════

@app.post(
    "/bad/criarEnvio",
    tags=["🔴 2 | Status Codes"],
    summary="❌ Criação que sempre retorna 200 — erros se escondem no corpo",
    description="""
**Problema: HTTP `200` para sucesso E para falha.**

- Cliente não pode confiar no status code — precisa parsear o JSON para saber se funcionou
- Monitoramento baseado em status codes (APM, alertas, SLOs) fica cego
- Retries automáticos não conseguem distinguir sucesso de falha
- **Esse é o antipadrão mais comum em sistemas legados e integrações corporativas**

**→ 50% de chance de simular falha disfarçada de `200`.**
""",
)
def bad_criar_envio(envio: EnvioCreate):
    if coin_flip():
        return {
            "success": False,
            "status":  "error",
            "message": "Falha ao processar envio. Tente novamente.",
            "data":    None,
        }
    return {
        "success": True,
        "status":  "ok",
        "data":    {"id": str(uuid.uuid4())[:8].upper(), **envio.model_dump()},
    }


@app.delete(
    "/bad/deletarEnvio/{envio_id}",
    tags=["🔴 2 | Status Codes"],
    summary="❌ DELETE que retorna 200 mesmo para IDs inexistentes",
    description="""
**Problemas:**

- Retorna `200` independente se o recurso existe — cliente não sabe se deletou algo real
- O correto é `204 No Content` (sucesso sem corpo) ou `404 Not Found` (não existia)
- Sistemas de auditoria não conseguem distinguir deleção real de tentativa sobre nada

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_delete_envio(envio_id: str):
    if coin_flip():
        return {"status": "error", "message": "Falha ao deletar", "id": envio_id}
    return {"status": "ok", "message": f"Envio {envio_id} deletado (talvez existisse, talvez não)"}


# ── CORRETOS ──────────────────────────────────────────────────────────────────

@app.post(
    "/v1/envios",
    tags=["🟢 2 | Status Codes"],
    status_code=201,
    summary="✅ POST correto: 201 Created + header Location",
    description="""
**Por que está certo:**

- `201 Created` — informa sem ambiguidade que um recurso novo foi criado
- Header `Location` aponta para o recurso criado — padrão RFC 7231
- Erros retornam status semânticos: `400`, `409`, `422`, `500`
- Monitoramento consegue contar sucessos vs falhas diretamente pelo status code
""",
)
def good_criar_envio(envio: EnvioCreate):
    novo_id = str(uuid.uuid4())[:8].upper()
    return JSONResponse(
        status_code=201,
        headers={"Location": f"/v1/envios/{novo_id}"},
        content={
            "id":         novo_id,
            "origem":     envio.origem,
            "destino":    envio.destino,
            "peso_kg":    envio.peso_kg,
            "descricao":  envio.descricao,
            "status":     "aguardando_coleta",
            "criado_em":  datetime.now().isoformat(),
        },
    )


@app.delete(
    "/v1/envios/{envio_id}",
    tags=["🟢 2 | Status Codes"],
    summary="✅ DELETE correto: 204, 404 ou 409 com semântica clara",
    description="""
**Por que está certo:**

- `204 No Content` — deleção bem-sucedida sem corpo (RFC semântico)
- `404 Not Found` — recurso não existia (use `envio_id = NOTFOUND`)
- `409 Conflict` — não pode deletar envio em andamento (use `envio_id = EMTRANSITO`)
- Cada cenário mapeado para um status único e interpretável por máquina
""",
)
def good_delete_envio(envio_id: str):
    if envio_id.upper() == "NOTFOUND":
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Envio '{envio_id}' não encontrado"},
        )
    if envio_id.upper() == "EMTRANSITO":
        raise HTTPException(
            status_code=409,
            detail={"error": "conflict", "message": "Envio em trânsito não pode ser deletado"},
        )
    return JSONResponse(status_code=204, content=None)


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 3 — PAGINAÇÃO
# ═════════════════════════════════════════════════════════════════════════════

@app.get(
    "/bad/todosOsRastreamentos",
    tags=["🔴 3 | Paginação"],
    summary="❌ Sem paginação: dump de tabela inteira",
    description="""
**Problema: retorna tudo, sempre.**

- Em produção com 500 k registros: query demora, banco sofre, resposta tem 200 MB
- Cada request compete por recursos com todos os outros usuários
- Clientes móveis recebem dados que nunca vão usar (over-fetching extremo)
- O primeiro sinal de escala é essa query travando o banco — aula 3.10

**→ 50% de chance de simular timeout com `200` no corpo.**
""",
)
def bad_todos_rastreamentos():
    if coin_flip():
        return {
            "status":  "error",
            "message": "Query timeout — registros demais para retornar de uma vez",
            "data":    None,
        }
    # Simulação: 50 aqui, mas o aviso é real
    registros = [
        {"envio_id": str(i), "eventos": _eventos(str(i))}
        for i in range(1, 51)
    ]
    return {
        "rastreamentos": registros,
        "aviso":         "⚠️ Em produção este endpoint retorna 500.000 registros",
        "total_real":    500000,
    }


@app.get(
    "/bad/rastreamentos",
    tags=["🔴 3 | Paginação"],
    summary="❌ Paginação por offset — lenta em tabelas grandes",
    description="""
**Problema: paginação por OFFSET/SKIP.**

- `OFFSET 499900 LIMIT 100` faz o banco **ler e descartar** 499.900 linhas
- Performance piora linearmente — página 1 é rápida, página 5000 é lenta
- Se alguém inserir um registro durante a paginação, dados pulam ou duplicam entre páginas
- Parâmetros `skip`/`take` em vez de `page`/`limit` — convenção ruim

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_paginacao_offset(skip: int = 0, take: int = 10):
    if coin_flip():
        return {"status": "error", "message": "Erro na paginação", "data": None}
    return [
        {"envio_id": str(skip + i), "eventos": _eventos(str(skip + i))}
        for i in range(take)
    ]


# ── CORRETOS ──────────────────────────────────────────────────────────────────

@app.get(
    "/v1/rastreamentos",
    tags=["🟢 3 | Paginação"],
    summary="✅ Paginação por cursor: O(1) em qualquer volume",
    description="""
**Por que está certo:**

- Cursor opaco (token) — banco busca a partir de um índice, sem escanear registros anteriores
- Performance **constante** na página 1 ou na página 50.000
- `has_next` + `next_cursor` formam um loop de paginação seguro e completo
- Filtros via query param evitam over-fetching
- `limit` com teto de 100 protege o servidor de requests abusivos
""",
)
def good_rastreamentos(
    limit:       int = Query(20, ge=1, le=100,   description="Itens por página (máx 100)"),
    cursor:      Optional[str] = Query(None,      description="Cursor retornado pela página anterior"),
    envio_id:    Optional[str] = Query(None,      description="Filtrar por ID de envio"),
    data_inicio: Optional[str] = Query(None,      examples=["2024-01-01"], description="Filtrar a partir desta data"),
):
    items = [
        {"envio_id": str(i), "eventos": _eventos(str(i))}
        for i in range(1, limit + 1)
    ]
    next_cursor = str(uuid.uuid4()) if len(items) == limit else None
    return {
        "data": items,
        "pagination": {
            "limit":       limit,
            "cursor":      cursor,
            "next_cursor": next_cursor,
            "has_next":    next_cursor is not None,
        },
    }


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — IDEMPOTÊNCIA
# ═════════════════════════════════════════════════════════════════════════════

@app.post(
    "/bad/confirmarEntrega",
    tags=["🔴 4 | Idempotência"],
    summary="❌ POST sem proteção: retry de rede = confirmação duplicada",
    description="""
**Problema: sem Idempotency-Key.**

- Um timeout de rede faz o cliente retentar — gera duas confirmações para a mesma entrega
- Na LunaLog: transportadora com bug enviava 800 req/s — confirmações se multiplicavam
- Cada chamada a este endpoint gera um `confirmacao_id` diferente — sem memória
- Em sistemas de pagamento: isso significa cobrar duas vezes

**Chame este endpoint duas vezes com os mesmos parâmetros — observe os `confirmacao_id` diferentes.**

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_confirmar_entrega(envio_id: str, motorista_id: str):
    if coin_flip():
        return {"status": "error", "message": "Falha ao confirmar entrega", "data": None}
    return {
        "confirmacao_id": str(uuid.uuid4()),  # sempre diferente!
        "envio_id":       envio_id,
        "motorista_id":   motorista_id,
        "aviso":          "⚠️ ID muda a cada chamada — retries criam duplicatas",
    }


# ── CORRETO ───────────────────────────────────────────────────────────────────

@app.post(
    "/v1/confirmacoes",
    tags=["🟢 4 | Idempotência"],
    status_code=201,
    summary="✅ POST idempotente com Idempotency-Key no header",
    description="""
**Por que está certo:**

- Header `Idempotency-Key` (UUID gerado pelo cliente) identifica a intenção
- Segunda chamada com a mesma key retorna `200` com o resultado original — sem duplicar
- Header `Idempotency-Replayed: true` indica que a resposta veio do cache
- Seguro para retries automáticos, clientes com conexão instável e workers de fila

**Como testar:**
1. Chame com `Idempotency-Key: meu-uuid-fixo` — recebe `201`
2. Chame novamente com o mesmo key — recebe `200` com `Idempotency-Replayed: true`
3. Compare os `confirmacao_id` — são idênticos
""",
)
def good_confirmar_entrega(
    envio_id:    str,
    motorista_id: str,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(
            status_code=422,
            detail={
                "error":   "missing_idempotency_key",
                "message": "O header 'Idempotency-Key' é obrigatório para esta operação",
            },
        )

    if idempotency_key in _idempotency_store:
        return JSONResponse(
            status_code=200,
            headers={"Idempotency-Replayed": "true"},
            content=_idempotency_store[idempotency_key],
        )

    resultado = {
        "confirmacao_id":  str(uuid.uuid4()),
        "envio_id":        envio_id,
        "motorista_id":    motorista_id,
        "confirmado_em":   datetime.now().isoformat(),
    }
    _idempotency_store[idempotency_key] = resultado
    return JSONResponse(status_code=201, content=resultado)


# ═════════════════════════════════════════════════════════════════════════════
# SEÇÃO 5 — VERSIONAMENTO
# ═════════════════════════════════════════════════════════════════════════════

@app.put(
    "/atualizarCliente/{cliente_id}",
    tags=["🔴 5 | Versionamento"],
    summary="❌ API sem versão na URL — próxima mudança quebra todos",
    description="""
**Problema: ausência de versionamento.**

- Hoje o `body` aceita `{ "endereco": "Rua X, 100" }` — string
- Amanhã o time muda para `{ "endereco": { "rua": "...", "numero": "..." } }` — objeto
- **Todas as transportadoras integradas quebram no mesmo momento**
- Na LunaLog: 40 transportadoras com contrato ativo — coordenar atualização simultânea é inviável

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_atualizar_cliente(cliente_id: str, body: dict):
    if coin_flip():
        return {"status": "error", "message": "Falha ao atualizar cliente", "data": None}
    return {
        "id":      cliente_id,
        "updates": body,
        "aviso":   "⚠️ Sem versionamento — qualquer mudança de schema quebra integrações",
    }


@app.put(
    "/bad/v1/clientes/{cliente_id}/endereco",
    tags=["🔴 5 | Versionamento"],
    summary="❌ Versão na URL mas schema sem deprecation path",
    description="""
**Problema: versão na URL mas sem estratégia de evolução.**

- `/v1/` existe mas não há `/v2/` quando o contrato muda
- Não há headers de deprecação avisando clientes da mudança futura
- Não há changelog ou documentação de migração
- Clientes precisam monitorar documentação manualmente — na prática, não monitoram

**→ 50% de chance de retornar `200` com erro no corpo.**
""",
)
def bad_atualizar_endereco(cliente_id: str, endereco: EnderecoUpdate):
    if coin_flip():
        return {"status": "error", "message": "Erro ao atualizar endereço", "data": None}
    return {"id": cliente_id, "endereco": endereco.model_dump()}


# ── CORRETOS ──────────────────────────────────────────────────────────────────

@app.patch(
    "/v1/clientes/{cliente_id}",
    tags=["🟢 5 | Versionamento"],
    summary="✅ PATCH v1 com headers de deprecação quando necessário",
    description="""
**Por que está certo:**

- PATCH para atualização **parcial** — só os campos enviados são alterados
- Headers `X-API-Version` e `X-API-Changelog` informam contexto ao cliente
- Quando uma nova versão é lançada, `Deprecation: true` + `Sunset` avisam com antecedência
- v1 continua funcionando enquanto clientes migram para v2 no próprio ritmo
""",
)
def good_atualizar_cliente_v1(cliente_id: str, updates: EnvioPartialUpdate):
    return JSONResponse(
        status_code=200,
        headers={
            "X-API-Version":   "v1",
            "X-API-Changelog": "https://docs.lunalog.com/api/changelog",
            "Deprecation":     "false",
        },
        content={
            "id":                cliente_id,
            "updates_aplicados": updates.model_dump(exclude_none=True),
            "atualizado_em":     datetime.now().isoformat(),
        },
    )


@app.get(
    "/v2/clientes/{cliente_id}",
    tags=["🟢 5 | Versionamento"],
    summary="✅ v2 coexiste com v1 — contrato melhorado sem breaking change",
    description="""
**Por que está certo:**

- `/v2/` coexiste com `/v1/` — clientes antigos continuam funcionando sem alteração
- Schema melhorado: `contatos` é array, `endereco` é objeto estruturado
- Header `Deprecation` em `/v1/` com data de `Sunset` avisando prazo de migração
- `_links` (HATEOAS) orienta o cliente sobre recursos relacionados
- A transição é opt-in — cliente migra quando estiver pronto
""",
)
def good_get_cliente_v2(cliente_id: str):
    return JSONResponse(
        status_code=200,
        headers={
            "X-API-Version": "v2",
            "Deprecation":   "@1767225600",
            "Sunset":        "Mon, 01 Jan 2026 00:00:00 GMT",
            "Link":          f'</v1/clientes/{cliente_id}>; rel="predecessor-version"',
        },
        content={
            "cliente": {
                "id":           cliente_id,
                "nome":         "Transportadora Silva Ltda",
                "documento":    "12.345.678/0001-90",
                "contatos":     [
                    {"tipo": "email",    "valor": "ops@silva.com.br"},
                    {"tipo": "telefone", "valor": "+55 11 91234-5678"},
                ],
                "endereco": {
                    "rua":    "Av. Brasil",
                    "numero": "1500",
                    "cidade": "São Paulo",
                    "estado": "SP",
                    "cep":    "01310-100",
                },
                "ativo":       True,
                "criado_em":   "2023-03-15T10:00:00",
            },
            "_links": {
                "self":   f"/v2/clientes/{cliente_id}",
                "envios": f"/v1/envios?cliente_id={cliente_id}",
                "v1":     f"/v1/clientes/{cliente_id}",
            },
        },
    )
