---
name: langgraph-agents
description: >
  Use when the user mentions LangGraph, StateGraph, graph.py, or a LangGraph
  adapter. Canonical skill is agent-orchestration — runtime is a port, not the
  domain.
---

# LangGraph é adapter

**REQUIRED SUB-SKILL:** `agent-orchestration` (spec) e `orchestration-runtime` (ativação).

LangGraph é um framework multi-agente. Compila `GraphSpec` em `infrastructure/adapters/langgraph`. Não desenhe o produto em `StateGraph`. CrewAI é o outro framework multi-agente da mesma porta (ponte `crewai-agents`). Make.com é automação de processos. In-process também é adapter. A skill `orchestration-runtime` pergunta qual, e implementa **um**. Não instale LangGraph “para depois trocar por CrewAI” nem por Make. Cenário na conta Make: ponte `make-scenarios`.

O spec continua em `specs/<job>/` (`agent-orchestration`). `graph.py` do spec monta `NodeSpec`/`EdgeSpec` **sem** SDK. Funções de node só existem se têm corpo. `StateGraph.add_node` / `add_edge` ficam no adapter.

Proibido: `from langgraph.graph import StateGraph` em `core/`, `application/` ou `specs/`.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Li e marquei a conferência de `agent-orchestration` e `orchestration-runtime`
- [ ] LangGraph é o runtime escolhido na ADR — não um ensaio do CrewAI nem do Make
- [ ] `StateGraph` só em `infrastructure/adapters/langgraph`; spec sem SDK
- [ ] `graph.py` / `nodes/` só com corpo; sem `node.py`/`edge.py` vazios
