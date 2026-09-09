---
name: mcp-servers
description: >
  Use when exposing a product to Grok, Cursor, ChatGPT or any MCP host, adding
  a custom connector, Streamable HTTP MCP, MCP_ENABLED, MCP_BEARER,
  MCP_TENANT_ID, or when the user mentions MCP server, grok.com/connectors,
  or remote MCP. For each tool, catalog, profile, or exposing an agent
  journey: mcp-tools. Agent spec/runtime: agent-orchestration +
  orchestration-runtime.
---

# Servidor MCP

MCP é **outra borda** do mesmo produto, não um segundo backend. O processo, o transporte e a descoberta vivem aqui. O que entra em `tools/list`: skill `mcp-tools`.

**REQUIRED SUB-SKILL:** `http-apis` (contrato HTTP), `mcp-tools` (cada tool), `auth` (emissor `connector`). Agente: `agent-orchestration` + `orchestration-runtime` — o `/mcp` chama o mesmo runtime; não nasce um segundo motor.

Nascer o agente **sem** esta borda, quando o produto tem conector, é o mesmo defeito de “ligo a guarda depois”. Default off. Ligar é env, não um PR de arquitetura.

## Transporte

Para Grok / xAI remote MCP: **Streamable HTTP** (SSE legado só se o host exigir). Path `/mcp` no **mesmo** FastAPI da API (`/mcp` é operação, não `/api/v1`). URL **pública** em produção. `localhost` é rejeitado na nuvem — túnel só em dev.

Stateless. Sem sessão mágica no processo. Respostas `/mcp`: `Cache-Control: no-store`.

## Liga / desliga

| Env | Papel |
|-----|--------|
| `MCP_ENABLED` | default **off**. Off → `tools/list` vazio; o processo HTTP sobe. Não é lista de nomes de tool |
| `MCP_BEARER` | obrigatório se enabled; senão o startup **recusa** |
| `MCP_TENANT_ID` | tenant do `Principal` connector; obrigatório se enabled |

Valores lidos no composition/settings e **injetados** no adapter. `os.environ` no domínio ou no use case é achado. Sem token no request → `401` + `WWW-Authenticate: Bearer`. Skill `auth`.

## Descoberta

`initialize` + `tools/list`. A lista deste processo = união dos **perfis** montados. Env só liga perfis já aprovados no código — não nomes soltos de tool. Conteúdo de cada tool: `mcp-tools`.

Host que pede `allowed_tools` deve poder restringir. Perfil no servidor **e** allowlist no host: os dois.

## Grok (norte de plataforma)

1. API de produto em `/api/v1` (skill `http-apis`).
2. Borda MCP em `/mcp` (Streamable HTTP) no **mesmo** composition root — no mesmo commit que o agente, default off.
3. Request sem token: `401` (Bearer de serviço no primeiro corte; PKCE quando o host público exigir — `auth`).
4. Admin cola a URL em grok.com/connectors → Custom.
5. Tools aparecem no host: OAuth/Bearer uma vez, depois chamada sob demanda.

## Como exercitar (dev)

Mesmo factory da API. Não crie um processo “mcp”:

```text
MCP_ENABLED=true MCP_BEARER=<token> MCP_TENANT_ID=<tenant> \
  uvicorn <pkg>.presentation.http.app:create_http_app --factory \
  --host 127.0.0.1 --port <dev>
```

Provar, nesta ordem: `GET /health` 200; `POST /mcp` sem Bearer → 401; `initialize`; `tools/list` = só o perfil (sem `run_agent`, sem capacidade só de catálogo); `tools/call` com `tenant_id` no body → 400; turno + mesma `idempotency_key` = replay.

## Red flags

- Segundo backend “só para MCP”
- stdio como único transporte para conector na nuvem
- Segredo na query string `?token=`
- Env publicando nomes arbitrários de tool
- Composition root distinto da API
- `MCP_ENABLED=true` sem bearer e tenant no startup
- `/mcp` numa fase 2 depois do spec do agente
- Adapter MCP lendo `os.environ` (settings no composition)

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Streamable HTTP em `/mcp` no mesmo FastAPI; `Cache-Control: no-store`
- [ ] `MCP_ENABLED` default off; ligado exige `MCP_BEARER` + `MCP_TENANT_ID` no startup
- [ ] Sem token → 401; auth `connector` (`auth`); valores injetados, não `getenv` no domínio
- [ ] Este processo monta só perfis aprovados; env não inventa tool
- [ ] Exercício vivo: health, 401, initialize, tools/list, call, replay — ou TestClient equivalente
- [ ] Conferência de `mcp-tools` marcada para cada tool/jornada deste servidor
