---
name: reliable-messaging
description: >
  Use when publishing domain events, adding an event bus, choosing RabbitMQ,
  Redis Streams or Azure Service Bus, dual-write, outbox, inbox, DLQ,
  at-least-once delivery, or when a use case would call a broker inside the
  same transaction as SQL. Worker process: background-workers. Cache is
  cache-ports — not this skill.
---

# Mensageria confiável

O domínio **não** conhece fila, exchange, ACK nem cliente do broker. Publica um fato via porto. A entrega é **at-least-once**. Exactly-once não se promete.

**REQUIRED BACKGROUND:** `AGENTS.md` (eventos, outbox, RPO). Consumer: `background-workers`. Cache/TTL: `cache-ports` (mesmo Redis ≠ o mesmo porto).

## Antes de implementar — pergunte

Se o produto **ainda não** tem broker escolhido em ADR/`AGENTS.md`, **pare e pergunte uma vez**:

> Qual provedor de eventos neste produto?
> 1. Redis Streams
> 2. RabbitMQ
> 3. Azure Service Bus (Microsoft)
> 4. Outro (nomeie)

Implemente **só** a resposta. Porto + outbox + inbox já. Segundo adapter só com segundo ambiente **real**. Três adapters “por se acaso” é YAGNI.

Se a resposta já está na conversa (“quero RabbitMQ”), não pergunte de novo.

## Forma

```
use case  →  outbox (mesma transação do agregado)
                 ↓
            relay (processo)  →  EventPublisherPort  →  broker
                                                      ↓
consumer  →  inbox (unique)  →  use case idempotente
```

Evento = fato passado (`case.created`). Comando = intenção dirigida. Proibido `entity.updated`.

Envelope versionado: `event_id`, `event_type`, `event_version`, `occurred_at` UTC, `producer`, `correlation_id`, `causation_id`, `trace_id`, `tenant_id`, `subject_id` (agregado do produtor), `payload` mínimo. Sem telefone, relato, segredo, token.

## Outbox / inbox

- **Outbox:** insert na **mesma** transação da mutação.
- **Relay:** processo à parte. Crash entre publicar e marcar = redelivery.
- **Inbox:** unique `(consumer, event_id)`. ACK **depois** do efeito.
- A claim da inbox e o efeito local são uma unidade atômica: mesma transação, ou estado
  `processing/completed` com lease recuperável. Persistir “já vi” antes do efeito e depois
  fazer `requeue` transforma a segunda entrega em perda silenciosa.
- Retry + jitter + teto; depois **DLQ** + replay. A política vive no **adapter**, não no use case.
- Ordem só por agregado quando o requisito pede.

Inbox: o **porto** (`remember`) pode viver na plataforma. O adapter SQL da inbox mora no bounded context **dono da tabela**. Pacote de plataforma **não** faz `INSERT INTO agents.inbox` (nem o schema de outro BC).

Fábrica do fato (`order.created`, `message.received`, producer default) mora no **serviço produtor**. Envelope genérico (campos, bloqueio de PII) mora em `packages/platform/events/`. Inbox Memory+porto em `platform/inbox/`. Nome estável do tipo, se compartilhado, em `packages/contracts`. Nenhum `.py` de capacidade na raiz do pacote.

## Porto

```
EventPublisherPort.publish(stream, envelope) -> id
EventPublisherPort.subscribe(stream, group, consumer) -> async iter (handle, envelope)
EventPublisherPort.checkpoint / ack(handle)
EventPublisherPort.close()
```

Factory no composition root: `provider` + `endpoint` + `destination`. Trocar o broker não mexe em `application/` nem no envelope. Codec JSON do envelope no adapter. Prefetch ≤ semáforo `queue`.

`MemoryEventPublisher` no teste de use case. Contract test do adapter escolhido (container).

## Adapters (implemente o escolhido)

I/O **async**. Segredo na URL/connection string: env, não git. Startup falha se o endpoint falta. Timeout em toda operação. Drain: para de puxar, ACK/NACK o in-flight (`background-workers`).

### Redis Streams

- `XADD` com `MAXLEN` aproximado (teto da fila). `XGROUP CREATE` MKSTREAM. `XREADGROUP` BLOCK. `XACK` no checkpoint. `XAUTOCLAIM` para mensagem órfã (idle).
- Consumer group = grupo lógico; consumer name = instância do worker.
- Prefixo de chave por ambiente (`env:`). Cluster: cliente cluster, não standalone.
- DLQ: stream irmão `:dlq` + ACK da original.
- Keepalive TCP curto em Redis gerenciado (senão o BLOCK fica num socket morto).

### RabbitMQ

- Exchange **fanout durable** por stream lógico. Queue durable `{stream}.{group}`, bind, `prefetch`.
- Publish **persistent**. ACK manual depois do inbox. Reject+requeue se o worker cair no meio.
- DLQ: exchange/queue `{stream}.dlq` + `x-dead-letter-exchange` na fila de trabalho. `reject(requeue=False)` **é** o caminho para a DLQ.
- **`reject(requeue=True)` não incrementa `x-death`.** Contar tentativas em header (`x-retry-count`) ou republicar numa fila de atraso (`expiration` / TTL + DLX de volta à fila de trabalho). No teto: nack sem requeue → DLQ. Backoff exponencial **com jitter** no adapter.
- URL do broker injetada; adapter recusa vazio. `getenv` só na composition (`RABBITMQ_URL`).
- Conexão `connect_robust`. Um channel com lock; não compartilhe channel entre tasks sem proteção.
- Nomes físicos no adapter; o domínio fala `stream` / `group`.

### Azure Service Bus (Microsoft)

- Topic = destination da config. Subscription = `{prefix}.{stream}` (canal filtrado; workers competem nela).
- `message_id` = `event_id`. `subject` / property = stream lógico. Lock renew no in-flight longo.
- Complete = checkpoint. Dead-letter nativo da subscription depois do teto.
- Credencial: connection string **ou** identidade gerenciada. Nunca as duas divergindo.
- Event Hubs só se o volume for stream de ingestão (CDC); work events cabem no Service Bus. Não misture os dois no mesmo porto.

## Red flags

- Implementar os três adapters no mesmo PR
- `redis.xadd` / `basic_publish` dentro do `commit()` do use case
- Redis Streams usado como cache (`cache-ports`)
- Consumer sem inbox; ACK antes de persistir
- `remember(event_id)` commitado antes do efeito, seguido de retry que trata a nova entrega como concluída
- Evento com PII; `subject_id` = pessoa
- Exchange/queue não durable; prefetch ilimitado
- SQL de inbox / fábrica de evento de BC no pacote de plataforma
- `envelope.py` / `ports.py` / `inbox.py` na raiz do platform (a capacidade é pasta)
- Retry por `requeue=True` confiando em `x-death` (teto nunca dispara; sem jitter vira tempestade)

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Provider perguntado (ou já decidido); **um** adapter
- [ ] Outbox na mesma transação; relay à parte; inbox unique
- [ ] ACK depois do efeito; DLQ real no teto; backoff+jitter no adapter; prefetch limitado
- [ ] Teste de janela de falha: crash depois da claim e antes do efeito; a 2ª entrega conclui o efeito uma vez
- [ ] Inbox SQL no BC dono da tabela; fábrica do fato no produtor; envelope genérico na plataforma
- [ ] Envelope versionado; sem PII; `subject_id` = agregado
- [ ] Porto estável; factory no composition root; I/O async
- [ ] Contract test do adapter escolhido; Memory* no use case
- [ ] Cache, se existir, é `cache-ports` — outro porto
