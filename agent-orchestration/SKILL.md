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

Tenda: Make.com é o **candidato** (ADR-005), não decisão automática e não segundo runtime “por se acaso”. Stockfy: LangGraph no adapter. A pasta do agente é a mesma nos dois.

**REQUIRED BACKGROUND:** `AGENTS.md` hexagonal + `persistence-ports`. Banco e LLM são portas.

## Um agente no v1 (Tenda)

O primeiro lançamento tem **um** agente: `conversational.complaint_intake`. Coleta no canal, confirma, publica `intake.completed`. Não existe `conversational/general` + `specialists/support`.

| Tentação | Por que não |
|----------|-------------|
| `general` roteando para `support` | um só trabalho cognitivo: conduzir a coleta. ADR-004 rejeitou “agente geral para tudo” |
| `specialist/support` como primeiro agente | em stockfy, specialist = pipeline operacional (onda, NF), não conversa. Suporte/escala humana **não** é outro LLM |
| Agente de escalonamento | HITL na **mesma** conversa (operador de canal) ou fila em `cases` depois do caso. Determinístico |

Escalonar para humano: `PendingInteraction` / atribuição de operador, não um segundo manifest. Depois do caso: triagem institucional, não agente.

Segundo agente só com bounded context próprio (ex.: copiloto do backoffice) + ADR + porta de invocação com allowlist. Sem pasta `specialists/` vazia.

## Dois gêneros (quando houver o segundo caso)

| | Conversacional | Operacional |
|--|----------------|-------------|
| Turnos | vários, pausa/retoma, HITL | pipeline com início e fim |
| Estado | sessão + histórico | documento / lote / job |
| LLM | conduz a conversa | um node; o resto determinístico |
| Stockfy | `chatops/general` | `dataops/waves_analyst` |

Não copie a árvore `specialists/` do stockfy para ter “cara de multi-agent”.

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

`register.py` devolve o spec. O **adapter** (`make` ou `langgraph`) compila e executa turno. Checkpointer do provider não é SSOT: o banco do serviço é.

## Runtime

```
application  →  OrchestrationRuntimePort.execute_turn / pause / resume
core         →  spec + estado + guardas
infrastructure/adapters/<runtime>  →  Make scenario / StateGraph.compile
```

Capability matrix **antes** de aprovar o runtime (idempotência, pausa, callback autenticado, retomada). Sem fallback silencioso entre Make e LangGraph.

## Red flags

- `import langgraph` ou API Make no `core/` / `application/`
- SQL no `graph.py`
- Dois agentes conversacionais para o mesmo colaborador no v1
- Pasta `specialists/support` sem segundo domínio
- LLM decidindo escalonamento crítico, criação de caso ou confirmação
- Cenário Make como dono da regra
