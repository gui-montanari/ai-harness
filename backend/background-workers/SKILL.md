---
name: background-workers
description: >
  Use when adding a worker, job, scheduler, stream consumer, supervisor,
  graceful shutdown, or when a request handler would asyncio.create_task /
  BackgroundTasks / setTimeout to "return faster". Also when splitting API
  from background work. Events: reliable-messaging. Persistência: persistence-ports.
---

# Workers em processo próprio

Trabalho durável **não** nasce no request HTTP. Enfileira (outbox) e responde. O worker é outro processo, **mesma imagem**, `command` diferente. Composition root compartilhado — senão a API e o worker divergem de adapter.

**REQUIRED BACKGROUND:** `AGENTS.md` §8.2–8.3. Fila/outbox: `reliable-messaging`.

## Recorte

| Processo | Faz | Não faz |
|----------|-----|---------|
| API | aceita, autentica, persiste intenção, responde | LLM, mídia, fan-out, `create_task` de efeito |
| Worker | consome, executa use case, ACK | servir HTTP de produto |
| Job | periódico, single-flight, idempotente por entidade+marco | timer em memória, “um de cada vez” via lock no processo |

Escala: réplicas do worker. Estado no banco/fila, nunca na RAM. Prefetch ≤ semáforo do recurso.

## Ciclo de vida

1. SIGTERM → para de puxar.
2. Termina in-flight até um deadline (`stop_grace_period` ≥ esse prazo).
3. NACK o resto. Fecha Redis/HTTP. `engine.dispose()`.
4. Orquestrador recria (`restart: unless-stopped` / `Always`).

Sem handler de SIGTERM, o kill corta no meio e a mensagem some **ou** duplica sem inbox. Os dois são achado.

Leader lock **durável** (banco/Redis com TTL) para job que não admite dois ao mesmo tempo. Lock em memória de uma instância não conta.

Exclusividade por agregado: no máximo um processamento em voo por conversa/caso — no banco, não por sticky routing.

## Saúde

- **Liveness:** processo morto. Não depende de Redis/DB (blip do dependente não mata o cluster).
- **Readiness:** pode puxar trabalho? Olha a fila/engine. Worker “vivo” que não consome é mentira.

Um container = um processo visível. Supervisor interno só se o orquestrador não puder; ainda assim o PID 1 é o supervisor, não um `nohup`.

## Red flags

- `asyncio.create_task` / `BackgroundTasks` / thread no handler “para não travar”
- Worker e API com factories de engine/Redis diferentes
- Job com `while True: sleep` sem lock durável
- ACK antes do efeito; restart sem idempotência
- Liveness que pinga o banco
- Dois consumidores do mesmo agregado sem exclusividade

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Trabalho durável fora do request; API ≠ worker; mesma imagem
- [ ] Composition root compartilhado
- [ ] SIGTERM: para de puxar, drena, NACK, dispose
- [ ] Job com lock durável; exclusividade por agregado no banco
- [ ] Liveness ≠ readiness; restart no orquestrador; idempotência no reprocessamento
