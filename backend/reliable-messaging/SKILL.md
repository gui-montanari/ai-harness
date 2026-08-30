---
name: reliable-messaging
description: >
  Use when publishing domain events, adding an event bus, Redis/Kafka/NATS
  stream, dual-write, outbox, inbox, DLQ, at-least-once delivery, or when a
  use case would call Redis/broker inside the same transaction as SQL. Worker
  process: background-workers. Auth of the consumer: auth.
---

# Mensageria confiável

O domínio **não** conhece fila, exchange, ACK nem cliente do broker. Publica um fato via porto. A entrega é **at-least-once**. Exactly-once não se promete.

**REQUIRED BACKGROUND:** `AGENTS.md` (eventos, outbox, inbox, RPO). Processo que consome: `background-workers`.

## Forma

```
use case  →  outbox (mesma transação do agregado)
                 ↓
            relay (processo)  →  EventPublisherPort  →  broker
                                                      ↓
consumer  →  inbox (unique)  →  use case idempotente
```

Evento = fato passado (`case.created`). Comando = intenção dirigida. Proibido `entity.updated`.

Envelope versionado: `event_id`, `event_type`, `event_version`, `occurred_at` UTC, `producer`, `correlation_id`, `causation_id`, `trace_id`, `tenant_id`, `subject_id` (agregado do produtor), `payload` mínimo. Sem telefone, relato, segredo, token. `tenant_id` não é default.

## Outbox / inbox

- **Outbox:** insert na **mesma** transação da mutação. Sem isso é dual-write.
- **Relay:** processo à parte (`background-workers`). Lê pendentes, publica, marca enviado. Crash entre publicar e marcar = redelivery — o consumidor aguenta.
- **Inbox:** unique `(consumer, event_id)`. Handler idempotente. ACK **depois** do efeito persistido.
- Retry com backoff + jitter; teto; depois **DLQ** inspecionável + replay controlado.
- Ordem só por agregado, quando o requisito pede — nunca “a fila é FIFO global”.

## Porto de transporte

`EventPublisherPort.publish` / `subscribe` / `checkpoint`. Factory no composition root escolhe Redis Streams, Kafka, NATS **pela config**. Trocar o broker não mexe em `application/` nem no envelope.

O relay **não** contém regra. Make.com / worker genérico não é o dono do fato.

## Red flags

- `redis.xadd` / `bus.publish` dentro do `session.commit()` do use case
- Consumer sem inbox (o reprocessamento duplica cobrança)
- ACK antes de persistir
- Evento com PII ou conteúdo integral
- `subject_id` = identidade da pessoa (correlaciona casos)
- Dois publishers (outbox **e** publish direto “mais rápido”)
- Fila sem teto, sem DLQ, sem métrica de profundidade/idade

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Outbox na mesma transação da mutação
- [ ] Relay em processo à parte; inbox unique no consumidor
- [ ] ACK depois do efeito; handler idempotente
- [ ] Envelope versionado; `subject_id` = agregado; sem PII
- [ ] Retry + jitter + teto + DLQ; porto de transporte no composition root
