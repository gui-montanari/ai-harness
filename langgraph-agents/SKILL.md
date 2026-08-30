---
name: langgraph-agents
description: >
  Use when creating or changing a LangGraph agent, GraphSpec, conversational
  vs operational graph, graph.py, config.py, prompts folder, agent registry,
  specialist/sub-agent, or orchestration runtime adapter.
---

# Agentes (LangGraph)

LangGraph é **adapter**. O domínio descreve o fluxo em `GraphSpec` (nós, arestas, estado) sem importar `StateGraph`. Compilar é infra.

Referência de **forma de pastas**: stockfy-ai `services/stockfy-agents` (chatops conversacional vs dataops operacional). Não copie SDK no core, god-file de `Chat.tsx` mental, nem taxonomia de specialist sem segundo domínio real.

**REQUIRED BACKGROUND:** `AGENTS.md` hexagonal + `persistence-ports` (grafo não fala SQL).

## Dois gêneros

| | Conversacional | Operacional |
|--|----------------|-------------|
| Turnos | vários, pausa/retoma, HITL possível | pipeline com início e fim |
| Estado | sessão + histórico | documento / lote / job |
| Exemplo stockfy | `chatops/general` | `dataops/shipment_output`, `waves_analyst` |
| LLM | conduz a conversa | um node pontual; o resto é determinístico |

v1 com **um** agente conversacional: não crie `specialists/` vazia. Segundo agente = segundo bounded context **ou** sub-agente no mesmo gênero, com ADR.

## Pasta de um agente

```
<agente>/
  config.py          # LLMConfig por node — SSOT de modelo/temperatura
  graph.py           # monta GraphSpec; thin; injeta nodes
  state.py           # estado tipado do turno/pipeline
  register.py        # composition root deste agente; recebe ports
  prompts/           # system.md, guardrails.md, skills/*.md — versionados
  nodes/             # só se o pipeline tiver passos próprios (operacional)
  tools/             # tools tipadas, allowlist, uma função = uma tool
```

`register.py` recebe `LLMRuntimePort`, repositórios, relógio. Devolve `GraphSpec`. O worker chama o registry explícito no startup — sem auto-discovery.

Prompts são arquivos, não string solta no node. Versão do prompt entra no trace da execução.

## Camadas

```
application  →  OrchestrationRuntimePort.execute_turn(...)
core         →  GraphSpec, estado, invariantes
infrastructure/adapters/langgraph  →  StateGraph.compile(spec)
```

`core` / `application` **não** importam `langgraph`, SDK de LLM, SQLAlchemy, Redis. Checkpointer do LangGraph não é a SSOT: o banco do serviço é.

Conversacional compartilhado (load_history → llm_turn → tools → terminal) vive **uma vez** no adapter; o agente só parametriza estado e nodes.

## Operacional vs conversa

Cálculo factual (prazo, ocupação, SLA) **não** passa pelo modelo. No stockfy, `operational.py` do waves é determinístico. O grafo chama isso como node/tool, não como “deixe o LLM somar”.

Tools: schema, timeout, idempotency key, autorização por execução. Sem tool “acesso ao banco”.

## Red flags

- `from langgraph.graph import StateGraph` em `core/` ou `application/`
- SQL / session no `graph.py`
- Prompt inline de 200 linhas no node
- Specialist novo sem segundo domínio
- Auto-discovery de agentes
- Checkpointer LangGraph como única cópia da conversa
- LLM decidindo schema, idempotência ou criação de caso
