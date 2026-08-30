---
name: http-apis
description: >
  Use when creating or changing a REST/HTTP API, FastAPI/Nest route, OpenAPI
  contract, /api/v1 endpoint, webhook, health/ready probe, or when Pydantic/Zod
  would sit next to a handler. For MCP hosts use mcp-servers; for OAuth of LLM
  connectors use oauth-connectors.
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

`/health` e `/ready` **fora** de `/api/v1`. Webhook: `/api/v1/webhooks/<adapter>`, autentica o envelope **antes** de normalizar.

## MCP

Host de LLM (Grok, Cursor, …) não ganha regra própria. Skill `mcp-servers`: cada tool é um use case já existente, schema JSON de input, auth do conector (`oauth-connectors`). Sem SQL no handler MCP.

## Auth da API de produto

Bearer JWT / sessão interna. M2M: OAuth2 `client_credentials`. Tenant do **contexto**, nunca do body. Isso **não** é o OAuth de conector Grok — skill `oauth-connectors`.

## Red flags

- `BaseModel` no mesmo arquivo que o `@router`
- rota de negócio sem `/api/v1`
- use case chamado `*Service` com três verbos
- regra no webhook, no MCP ou no Make.com
- proxy de dev que apaga `/api/v1`
- OpenAPI gerado e ninguém consome
