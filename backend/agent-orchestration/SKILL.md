---
name: agent-orchestration
description: >
  Use when creating or changing a product agent, GraphSpec, WorkflowSpec,
  conversational vs operational flow, graph.py, config.py, prompts folder,
  Make.com scenario, LangGraph adapter, specialist/sub-agent, or runtime of
  agents. LangGraph and Make are adapters, not the domain.
---

# Orquestração de agentes

O fluxo é **declarativo e neutro** (`GraphSpec` / `WorkflowSpec`). Make.com, LangGraph ou outro runtime **compilam** isso no adapter. O domínio não importa SDK de Make nem `StateGraph`.

O runtime conhecido da empresa é o **primeiro candidato**, avaliado por capability matrix — não é decisão automática e não autoriza segundo runtime “por se acaso”. A pasta do agente é a mesma, qualquer que seja o adapter.

**REQUIRED BACKGROUND:** `AGENTS.md` hexagonal + `persistence-ports`. Banco e LLM são portas.

## Um agente no primeiro lançamento

Comece com **um** agente conversacional, identificado pela capacidade (`conversational.<job>`). Ele conduz a jornada, confirma e publica o fato. Não existe `conversational/general` + `specialists/support` para o mesmo trabalho.

| Tentação | Por que não |
|----------|-------------|
| `general` roteando para `support` | um só trabalho cognitivo. “Agente geral para tudo” infla prompt, tools e risco |
| `specialist/support` como primeiro agente | specialist = pipeline operacional (documento, lote, job), não conversa. Escala humana **não** é outro LLM |
| Agente de escalonamento | HITL na **mesma** conversa ou fila de operação depois do fato de negócio. Determinístico |

Escalonar para humano: `PendingInteraction` / atribuição de operador, não um segundo manifest. Depois do fato oficial: fila institucional, não agente.

Segundo agente só com bounded context próprio (ex.: copiloto autenticado interno) + ADR + porta de invocação com allowlist. Sem pasta `specialists/` vazia.

## Dois gêneros (quando houver o segundo caso)

| | Conversacional | Operacional |
|--|----------------|-------------|
| Turnos | vários, pausa/retoma, HITL | pipeline com início e fim |
| Estado | sessão + histórico | documento / lote / job |
| LLM | conduz a conversa | um node; o resto determinístico |
| Exemplo de pasta | `agents/intake/` | `agents/document_extract/` |

Não invente árvore `specialists/` só para ter “cara de multi-agent”.

## Pasta de um agente (agnóstica)

```
<agente>/
  config.py       # modelo/temperatura por node — SSOT; sem SDK de runtime
  graph.py        # monta GraphSpec/WorkflowSpec; injeta ports
  state.py
  register.py     # composition; recebe OrchestrationRuntimePort, LLM, repos
  prompts/        # .md versionados; versão no trace
  nodes/          # só pipeline operacional
  tools/          # schema, timeout, idempotency, allowlist
```

`register.py` devolve o spec. O **adapter** (`make`, `langgraph`, …) compila e executa turno. Checkpointer do provider não é SSOT: o banco do serviço é.

## Runtime

```
application  →  OrchestrationRuntimePort.execute_turn / pause / resume
core         →  spec + estado + guardas
infrastructure/adapters/<runtime>  →  scenario / StateGraph.compile
```

Capability matrix **antes** de aprovar o runtime (idempotência, pausa, callback autenticado, retomada). Sem fallback silencioso entre runtimes.

## Red flags

- SDK de runtime no `core/` / `application/`
- SQL no `graph.py`
- Dois agentes conversacionais para o mesmo usuário no primeiro lançamento
- Pasta `specialists/support` sem segundo domínio
- LLM decidindo escalonamento crítico, criação de registro oficial ou confirmação
- Cenário do orquestrador como dono da regra

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Spec neutro (`GraphSpec`/`WorkflowSpec`); SDK só no adapter
- [ ] Um agente conversacional no primeiro lançamento, se for o caso
- [ ] Registro explícito no startup; sem auto-discovery
- [ ] Título de conversa (se houver lista): use case após a 1ª resposta, ≤6 palavras
- [ ] Guardas de estado e de saída determinísticas; LLM não cria o fato oficial
- [ ] Checkpointer do runtime ≠ SSOT (banco do serviço)
