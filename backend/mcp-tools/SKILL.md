---
name: mcp-tools
description: >
  Use when adding or changing an MCP tool, publishing a capability or agent
  journey on a connector, choosing a specific tool versus a complete agent on
  the MCP server, allowlist, catalog vs profile, internal_probe, tool scopes,
  tenant_id in arguments, open_conversation, execute_turn, or run_agent.
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

O catálogo pode conter capacidades que o perfil **não** lista (ex.: `internal_probe` existe e **não** aparece em `tools/list`). Perfil da jornada de coleta = só a tool nomeada pelo resultado. `run_agent` não entra em nenhum dos dois. `allowed_specialist_keys` do conversacional **não** é perfil MCP — tools internas do grafo continuam fora de `tools/list`.

Escala: **N tools, poucos perfis, um processo**. Servidor novo só com fronteira operacional real (audiência, auth, ciclo de vida). Host `allowed_tools` **e** perfil no servidor — os dois. Tool nova = contrato versionado, não processo novo.

A mesma capacidade pode estar em HTTP e em um ou mais perfis MCP **sem** copiar o use case. Binding por superfície; regra uma vez.

## Binding

- Args → command de `application/`. Zero regra nova no handler MCP.
- Jornada de agente: o binding chama o use case de turno (`open_conversation` + `OrchestrationRuntimePort.execute_turn`). Sem WhatsApp, sem criar fato oficial.
- IDs do payload confrontam o `Principal`. Tenant do token (`MCP_TENANT_ID` / claim), **nunca** do body — se `tenant_id` vier no arguments, rejeite (400), não ignore.
- `idempotency_key` obrigatória no schema da jornada; mesma key = replay do runtime.
- Escrita ou efeito sensível: o host precisa poder exigir aprovação (`approval_required` ou equivalente).
- Assíncrono: resultado estruturado + `operation_id` (ou o correlator do produto). Não relatar o grafo.
- Timeout, retry e idempotência **herdados**. Sem `for _ in range` no binding.
- Retorno: `conversation_id`, `reply` já passado na guarda, flags. Sem draft, relato, prompt, path interno ou PII.

## Red flags

- `run_agent`, `execute_sql`, shell, `run_query`
- Publicar as tools internas de `agent-orchestration`
- Duplicar o use case “porque é MCP”
- Env com lista solta de nomes de tool
- Tool sem schema, sem scope, sem tenant
- Jornada que deixa o request MCP aberto
- Um perfil “deus” com o catálogo inteiro para todo host
- `internal_probe` (ou equivalente de catálogo) vazando em `tools/list`
- Binding que dispara canal ou cria caso oficial
- Aceitar `tenant_id` no arguments

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Grão certo: atômica **ou** início de jornada nomeada pelo resultado; nunca `run_agent`
- [ ] Use case já existe; binding = `open_conversation` + `execute_turn` na jornada; tenant do `Principal`
- [ ] Catálogo ≠ perfil; capacidade só de catálogo **não** entra em `tools/list`; env não inventa tool
- [ ] `tenant_id` no body rejeitado; `idempotency_key` obrigatória na jornada
- [ ] Schema estreito; scopes da capacidade; escrita com aprovação do host
- [ ] Retorno sem draft/PII; jornada não segura o request até o agente “terminar”
- [ ] Conferência de `mcp-servers` marcada se o servidor/transporte também mudou
