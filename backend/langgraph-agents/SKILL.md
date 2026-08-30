---
name: langgraph-agents
description: >
  Use when the user mentions LangGraph, StateGraph, graph.py, or a LangGraph
  adapter. Canonical skill is agent-orchestration — runtime is a port, not the
  domain.
---

# LangGraph é adapter

**REQUIRED SUB-SKILL:** `agent-orchestration`.

LangGraph compila `GraphSpec` em `infrastructure/adapters/langgraph`. Não desenhe o produto em `StateGraph`. Make.com ou outro orquestrador conhecido é outro adapter da mesma porta.

Proibido: `from langgraph.graph import StateGraph` em `core/` ou `application/`.
