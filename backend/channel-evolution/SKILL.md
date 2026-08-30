---
name: channel-evolution
description: >
  Use when adding or changing Evolution API, WhatsApp session webhook,
  sendText, apikey header, remoteJid, messages.upsert, EVOLUTION_BASE_URL,
  EVOLUTION_API_KEY, EVOLUTION_INSTANCE, or a channel outbound adapter.
  Official WABA/Twilio templates: messaging-gateway Twilio adapter.
  Agent turn: agent-orchestration.
---

# Canal Evolution

Evolution é **adapter de canal** no limite de mensageria. Não é o domínio de casos, não é o agente, não é o provider oficial de template/janela da Meta.

**REQUIRED BACKGROUND:** constituição `AGENTS.md` hexagonal. Spec do agente: `agent-orchestration` (não este recorte). Webhook HTTP: `http-apis`. Env: nomes de capacidade, zero hardcode.

## O que copiar (propriedades)

Porta pequena, composition escolhe o adapter, envelope bruto não vaza. Inbound normaliza; outbound envia texto aprovado.

| Peça | Mora | Não mora |
|------|------|----------|
| `ChannelOutboundPort.send(destination, text)` | `core/ports/` do messaging-gateway | caso, agente, UI |
| Normalize inbound | `adapters/evolution/webhook.py` | handler de turno |
| HTTP sendText | `adapters/evolution/outbound.py` | use case de coleta |
| Instância, URL, apikey | env no composition | repositório, log, evento |

## Env (SSOT `.env.example`)

```
EVOLUTION_BASE_URL=
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE=
EVOLUTION_TIMEOUT_SECONDS=20
```

Sem prefixo da marca do produto. Sem URL no adapter via `getenv`.

## Inbound

Webhook `POST /api/v1/webhooks/evolution`, header `apikey` comparado com timing-safe.

Evento típico: `messages.upsert`. Extrair:

- identidade → `remoteJid` split `@` → `sender_key` opaco para o domínio
- texto → `message.conversation` ou `extendedTextMessage.text`
- id → `key.id`

`fromMe: true` **não** entra no turno (eco do próprio envio).

O handler de turno recebe `(sender_key, text)` neutro. Nunca `remoteJid` em caso, evento ou log.

## Outbound

```
POST {EVOLUTION_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE}
Header: apikey
JSON: {"number": "<dígitos sem +>", "text": "<já passou na guarda de saída>"}
```

Timeout obrigatório. Destino/texto vazio falha fechado. Sem retry infinito. Sem circuit breaker no mesmo arquivo que o HTTP até haver segundo caso concreto.

O use case de canal: persiste intenção (append/outbox) **depois** gera o texto aprovado, **depois** `send`. Interromper entre send e registro não pode duplicar no reprocessamento — idempotency no envelope inbound já existe; outbound registra a intenção primeiro.

## O que não fazer (CRMAI e similares)

- Cliente de 1000 linhas com circuit breaker, retry e CRUD de instância no mesmo módulo
- Factory com registry global mutável
- `WhatsApp` no domínio de casos
- Evolution como “depois a gente troca pelo Twilio oficial” para templates da Meta
- Segredo no código ou no git

Twilio (WABA, template, janela) continua adapter **irmão**, mesma porta. Acrescentar canal = adapter novo, não if no agente.

## Conferência

- [ ] Porta `send` + normalize no messaging-gateway; domínio sem `remoteJid`
- [ ] Env `EVOLUTION_*` no `.env.example`; adapter sem `getenv`
- [ ] Inbound: apikey timing-safe; `fromMe` ignorado; turno recebe texto neutro
- [ ] Outbound: `sendText`, timeout, número sem `+`, texto já aprovado
- [ ] Testes: 401, skip fromMe, send posta o envelope, turno dispara `send`
- [ ] Sem cliente-deus, sem registry global, sem template Meta no Evolution
