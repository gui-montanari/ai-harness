---
name: crewai-agents
description: >
  Use when the user mentions CrewAI, a Crew, or a CrewAI adapter. Canonical
  skill is orchestration-runtime — CrewAI compiles the spec; it is not the
  domain. Not LangGraph (langgraph-agents). Not Make.com process automation
  (make-scenarios).
---

# CrewAI é adapter

**REQUIRED SUB-SKILL:** `agent-orchestration` (spec) e `orchestration-runtime` (ativação).

CrewAI é um framework multi-agente. Compila o mesmo `GraphSpec` em `infrastructure/adapters/crewai` (`Crew`, `Agent`, `Task`). Não desenhe o produto em Crew. LangGraph é o outro framework multi-agente da mesma porta. Make.com é automação de processos, outro adapter, não um multi-agente. A skill `orchestration-runtime` pergunta qual, e implementa **um**. Não instale CrewAI “para depois trocar por LangGraph”, nem os dois para parecer completo.

O spec continua em `specs/<job>/` (`agent-orchestration`). `graph.py` do spec monta `NodeSpec`/`EdgeSpec` **sem** SDK. Funções de node só existem se têm corpo. `Crew` / `Agent` / `Task` ficam no adapter. Persistência no `ConversationStore`, não na memória do Crew.

Proibido: `from crewai import Crew` em `core/`, `application/` ou `specs/`.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Li e marquei a conferência de `agent-orchestration` e `orchestration-runtime`
- [ ] CrewAI é o runtime escolhido na ADR — não um ensaio do LangGraph nem do Make
- [ ] `Crew` / `Agent` / `Task` só em `infrastructure/adapters/crewai`; spec sem SDK
- [ ] `graph.py` / `nodes/` só com corpo; sem `node.py`/`edge.py` vazios
