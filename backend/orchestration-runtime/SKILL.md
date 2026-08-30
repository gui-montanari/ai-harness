---
name: orchestration-runtime
description: >
  Use when activating or swapping an agent orchestration runtime, wiring
  OrchestrationRuntimePort, checking RuntimeCapabilities at startup, choosing
  in-process vs Make vs LangGraph, or when the user mentions execute_turn,
  checkpointer, runtime activation, or /orchestration-runtime. Spec of the
  agent: agent-orchestration. Worker process: background-workers. LLM text
  generation is a different port.
---

# Ativação do runtime de orquestração

O agente tem um **spec** (`agent-orchestration`). Esta skill é **como o motor que executa o spec é escolhido, ligado no startup e chamado no turno**. Sem isso o agente inventa `StateGraph` no use case ou sobe LangGraph “porque o outro produto tinha”.

**REQUIRED BACKGROUND:** constituição `AGENTS.md` hexagonal. Spec, um agente, guardas: `agent-orchestration`. Processo API ≠ worker: `background-workers`. LLM gera texto: porta própria, não este runtime.

Três coisas distintas — não misture:

| Peça | É | Não é |
|------|---|--------|
| Spec do agente | `GraphSpec` / `WorkflowSpec` | SDK |
| Runtime de orquestração | executa turno / pausa / retoma | o worker do SO |
| Processo | API ou worker (`background-workers`) | o grafo |

O mesmo composition root monta o runtime **uma vez**. API e worker **herdam**. Dois `LangGraphOrchestrator()` soltos (um na app, um no consumer) = drift.

## Antes de implementar — pergunte

Se o runtime **ainda não** está no ADR/`AGENTS.md`:

> Qual runtime de orquestração neste produto?
> 1. In-process determinístico (use case no próprio serviço — candidato do primeiro lançamento)
> 2. Make.com (candidato conhecido da empresa, se a capability matrix fechar)
> 3. LangGraph (adapter; spec continua neutro)
> 4. Outro (nomeie)

Implemente **um**. Segundo runtime só com capability **obrigatória** ausente no primeiro + ADR. Airflow, Celery beat ou “composite” extra não nascem para ter simetria de pasta.

In-process **é** runtime. Roteiro determinístico com guardas, HITL e persistência no banco do serviço já cumpre o primeiro lançamento. Não puxe LangGraph para “completar a arquitetura”.

## Ativação (indústria)

Ordem no startup — falha fechada:

1. Ler manifests dos agentes (`agent-orchestration`). Registro **explícito**.
2. Declarar `RuntimeCapabilities` **exigidas** pelo agente (checkpoint, HITL, tool calling, pause/resume, idempotência de turno).
3. Instanciar **um** adapter no composition root. Ele declara as capacidades **oferecidas**.
4. Se exigido ⊄ oferecido: **não sobe**. Log sem PII. Sem fallback silencioso para outro motor.
5. API e worker recebem a mesma instância (ou o mesmo builder).

```
application  →  OrchestrationRuntimePort
                execute_turn / pause / resume / cancel
core         →  spec + AgentTurnRequest / AgentTurnResult
infrastructure/adapters/<runtime>/  →  SDK
```

Porta pequena:

```
execute_turn(AgentTurnRequest) -> AgentTurnResult
pause(conversation_id)
resume(conversation_id, payload)
cancel(conversation_id)
```

`AgentTurnRequest` traz tenant, conversation_id, message_ref, idempotency key, sequence. Resultado tipado: reply aprovado pela guarda de **saída**, flags (HITL, intake_completed), sem objeto do SDK.

Checkpointer do provider (thread id, memory saver) **não** é SSOT. O banco do serviço de agentes é. Crash: retoma pelo estado persistido, não pela memória do grafo.

LLM é `LlmPort` (gerar texto / structured). O runtime **chama** a porta nos **turnos de modelo** com o prompt versionado (`agent-orchestration`). Não substitui a guarda determinística nem redige texto canônico (privacidade, recap, recusa).

## Adapters (quando escolhidos)

**In-process:** o use case de turno **é** o motor. Sem pasta `adapters/langgraph`. Sem `StateGraph`. Persistência e HITL já no domínio. Ativação = registrar o use case no composition root + capabilities que ele de fato oferece (HITL sim, tool calling do modelo talvez não).

**Make.com:** só depois da capability matrix. Cenário no adapter; regra canônica no serviço. Callback autenticado, idempotente, correlacionado. Make não escolhe tenant nem guarda saída.

**LangGraph:** `infrastructure/adapters/<runtime>/`. Compila `GraphSpec` → `StateGraph`. `interrupt` vira `PendingInteraction` no domínio, não um tipo do SDK vazando. Ponte: `langgraph-agents`.

Proibido: `from langgraph.graph import StateGraph` em `core/`, `application/`, `graph.py` do agente. O `graph.py` monta o **spec**.

## Relação com o processo

O runtime de orquestração **não** é o supervisor de filas. Consumidor, drain, restart: `background-workers`. O worker **chama** `execute_turn`. Supervisor que recria o processo não recria o spec.

## Red flags

- SDK de orquestração no use case ou no domínio
- Segundo motor “para ter LangGraph e Make”
- Capabilities declaradas e não verificadas no startup
- Checkpointer do provider como única cópia do estado
- LLM contornando guarda de estado ou de saída
- Dois builders (API vs worker) com configs diferentes
- Pasta `runtimes/` com regra de negócio
- Wrappers pass-through de porta sem o segundo adapter **e** sem check de capability — aí não há fronteira, só teatro

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Runtime perguntado (ou já no ADR); **um** adapter
- [ ] In-process aceito se a capability matrix do outro motor não fechou / não foi pedida
- [ ] `OrchestrationRuntimePort` no core; SDK só no adapter
- [ ] Capabilities exigidas ⊂ oferecidas; senão o processo não sobe
- [ ] Mesmo builder na API e no worker
- [ ] Banco do serviço é SSOT; checkpointer não é
- [ ] Spec e guardas continuam em `agent-orchestration`; worker em `background-workers`
