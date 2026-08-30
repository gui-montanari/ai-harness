---
name: mcp-tools
description: >
  Use when adding or changing an MCP tool, publishing a capability or agent
  journey on a connector, choosing a specific tool versus a complete agent on
  the MCP server, allowlist, catalog, server profile, tool scopes, or run_agent.
  For the MCP server itself (transport, /mcp, initialize) use mcp-servers.
  Internal graph tools: agent-orchestration.
---

# Tools na borda MCP

MCP **não** tem primitiva `agent`. O servidor (`mcp-servers`) só transporta. Esta skill decide **o que** entra em `tools/list`: tool atômica, jornada, ou nada.

Publicar é contrato de produto. Não é dump do grafo nem `run_agent(name, prompt)`.

**REQUIRED SUB-SKILL:** `mcp-servers` (transporte), `http-apis` (o mesmo use case já existe na API), `auth` (scopes no `Principal`). Agente interno: `agent-orchestration` — pasta `tools/` do grafo **não** se publica sozinha.

## Grão — o que o host enxerga

| O host precisa | Publicar | Não publicar |
|----------------|----------|--------------|
| Consulta ou comando determinístico | 1 tool atômica, nome de negócio (`list_cases`, `get_inventory_position`) | SQL, prompt, classe, node |
| Jornada longa, HITL, pipeline agentic | 1 tool de **início** (aceite + id correlacionável). Continuar / consultar estado = tools à parte, se o host precisar | Segurar a chamada MCP até o agente terminar |
| “O agente completo” | A **jornada** nomeada pelo resultado (`intake_order`, `analyze_picking`), no **perfil** da audiência | O kit interno do grafo; um executor genérico |

Nome estável, verbo+objeto. `inputSchema` JSON Schema estreito (`additionalProperties` fechado). A descrição é o contrato que o modelo lê: uma frase, parâmetros óbvios, o que **não** faz.

Efeito da tool (indústria, o mesmo da capacidade):

- leitura — síncrona, sem side-effect
- comando — mutação autorizada, idempotente
- jornada — aceita trabalho e devolve identificador; o worker executa (`background-workers`)

## Camadas — um fato, um dono

```
core           capacidade: efeito, scopes, idempotência
application    use case (HTTP e MCP chamam o mesmo)
adapter MCP    binding: JSON Schema → command; tenant do Principal
catálogo       o que *pode* ser publicado (allowlist explícita)
perfil         o que *este* servidor lista (uma audiência)
processo       env só habilita perfis já aprovados no código
```

Registrar o agente ou o use case **não** publica. Sem auto-discovery por pasta, convenção de nome ou “todas as tools do grafo”.

Escala: **N tools, poucos perfis, um processo**. Servidor novo só com fronteira operacional real (audiência, auth, ciclo de vida). Host `allowed_tools` **e** perfil no servidor — os dois. Tool nova = contrato versionado, não processo novo.

A mesma capacidade pode estar em HTTP e em um ou mais perfis MCP **sem** copiar o use case. Binding por superfície; regra uma vez.

## Binding

- Args → command de `application/`. Zero regra nova no handler MCP.
- IDs do payload confrontam o `Principal`. Tenant do token, nunca do body.
- Escrita ou efeito sensível: o host precisa poder exigir aprovação (`approval_required` ou equivalente).
- Assíncrono: resultado estruturado + `operation_id` (ou o correlator do produto). Não relatar o grafo.
- Timeout, retry e idempotência **herdados**. Sem `for _ in range` no binding.
- Retorno sem PII, token, path interno, prompt ou stack.

## Red flags

- `run_agent`, `execute_sql`, shell, `run_query`
- Publicar as tools internas de `agent-orchestration`
- Duplicar o use case “porque é MCP”
- Env com lista solta de nomes de tool
- Tool sem schema, sem scope, sem tenant
- Jornada que deixa o request MCP aberto
- Um perfil “deus” com o catálogo inteiro para todo host

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Grão certo: atômica **ou** início de jornada nomeada pelo resultado; nunca `run_agent`
- [ ] Use case já existe; binding só traduz; tenant do `Principal`
- [ ] No catálogo explícito **e** no perfil da audiência; env não inventa tool
- [ ] Schema estreito; scopes da capacidade; escrita com aprovação do host
- [ ] Jornada: aceite + id; trabalho no worker; retorno sem PII
- [ ] Conferência de `mcp-servers` marcada se o servidor/transporte também mudou
