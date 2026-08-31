---
name: http-apis
description: >
  Use when creating or changing a REST/HTTP API, FastAPI/Nest route, OpenAPI
  contract, /api/v1 endpoint, webhook, health/ready probe, or when Pydantic/Zod
  would sit next to a handler. For the MCP server use mcp-servers; for each MCP
  tool or agent journey use mcp-tools; for OAuth of LLM connectors use auth.
---

# APIs HTTP

**REQUIRED BACKGROUND:** constituição `AGENTS.md` §3.1, §3.3 e §8. Camadas e nomes não se reescrevem aqui.

A API é **apresentação**. Caso de uso vive em `application/`. MCP, CLI e worker **chamam o mesmo use case**.

## Árvore

```
presentation/
  schemas/                 # único BaseModel/Zod de borda
  http/
    app.py                 # factory, /health /ready
    v1/                    # routers; prefixo /api/v1
application/
  <verbo>.py               # execute
  commands/                # Command/Result — não HTTP
```

## Receita de um endpoint

1. Contrato no schema (`OrderCreateRequest` / `OrderResponse`).
2. Command em `application/commands/`.
3. Use case com teste unitário (RED).
4. Router em `http/v1/` — valida transporte, autentica, chama o use case, traduz erro.
5. OpenAPI nasce do schema. Cliente gerado no pipeline, ou o cliente artesanal é achado.

Rota pública exige consumidor e fonte de autoridade explícitos (requisito/ADR aceito). Não
publique endpoint de teste para simular provider. Identidade técnica (`sender_key`, tenant,
ator, reviewer) deriva do principal/envelope autenticado; nunca de body arbitrário. Endpoint
que devolve histórico ou capability token recebe threat model e testes negativos de enumeração,
personificação, cache e referrer.

`/health` e `/ready` **fora** de `/api/v1`. Webhook: `/api/v1/webhooks/<adapter>`, autentica o envelope **antes** de normalizar.

Factory ASGI (`--factory`): tenant, CORS e título vêm do env no start (`TENANT_ID`, `CORS_ORIGINS`, `APP_TITLE`). Não `app = create_http_app()` no import — quebra teste e crava default. `allow_origins=["http://localhost:5173"]` e `title="NomeDoProduto"` são hardcode.

## MCP

Host de LLM não ganha regra própria. Servidor: `mcp-servers`. Cada tool ou jornada: `mcp-tools` (o mesmo use case). Auth: skill `auth`.

## Auth

Skill `auth`. Borda HTTP autentica, converte para `Principal`, chama o use case. Tenant do contexto, nunca do body.

## Red flags

- `BaseModel` no mesmo arquivo que o `@router`
- rota de negócio sem `/api/v1`
- use case chamado `*Service` com três verbos
- regra no webhook, no MCP ou no Make.com
- proxy de dev que apaga `/api/v1`
- OpenAPI gerado e ninguém consome
- rota `publico-intencional` sem requisito/ADR e consumidor aprovado
- cliente escolhe identidade de canal, tenant, ator ou revisor
- CORS, título ou token cravados no `app.py`

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Schema em `presentation/schemas/`; Command em `application/commands/`
- [ ] Use case um verbo, com teste RED primeiro
- [ ] Rota de negócio em `/api/v1`; `/health` `/ready` na raiz
- [ ] Handler só traduz; authz no use case; tenant do contexto
- [ ] Toda rota pública cita a fonte que a autoriza e tem testes negativos; nenhuma rota de teste sobe em produção
- [ ] OpenAPI do schema; cliente gerado ou nenhum cliente artesanal
- [ ] CORS/título/tenant na factory via env; sem literal de produto
