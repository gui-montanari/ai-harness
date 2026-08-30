---
name: langgraph-agents
description: >
  Use when the user mentions LangGraph, StateGraph, graph.py, or a LangGraph
  adapter. Canonical skill is agent-orchestration — runtime is a port, not the
  domain.
---

# LangGraph é adapter

**REQUIRED SUB-SKILL:** `agent-orchestration` (spec) e `orchestration-runtime` (ativação).

LangGraph compila `GraphSpec` em `infrastructure/adapters/<runtime>`. Não desenhe o produto em `StateGraph`. Make.com ou in-process é outro adapter da **mesma** porta — skill `orchestration-runtime` pergunta qual, e implementa um.

Proibido: `from langgraph.graph import StateGraph` em `core/` ou `application/`.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Li e marquei a conferência de `agent-orchestration`
- [ ] `StateGraph` só em `infrastructure/adapters/langgraph`
