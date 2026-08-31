---
name: whatsapp-channel
description: >
  Use when adding or changing WhatsApp inbound/outbound, Evolution API,
  Twilio WhatsApp, WABA, sendText, templates, 24h window, remoteJid,
  MessageSid, X-Twilio-Signature, apikey, messages.upsert, ChannelOutboundPort,
  EVOLUTION_BASE_URL, TWILIO_AUTH_TOKEN, or a channel adapter. Agent turn:
  agent-orchestration. HTTP webhook: http-apis.
---

# WhatsApp — um canal, vários integradores

WhatsApp é o **canal**. Evolution, Twilio (WABA) e qualquer outro são **adapters** da mesma porta. O domínio de casos e o agente só vêem `sender_key` + `text` + `send(destination, text)`.

**REQUIRED BACKGROUND:** constituição `AGENTS.md` hexagonal. Turno do agente: `agent-orchestration`. Webhook: `http-apis`.

## Porta (única)

```
ChannelOutboundPort.send(destination, text) -> None
normalize_inbound(payload) -> { sender_key, text, provider_message_id }
```

Composition escolhe o adapter (`CHANNEL_ADAPTER=evolution|twilio`). Sem if de provider no use case, no agente ou no caso.

O conjunto permitido vem do requisito/ADR do produto. A existência desta skill não autoriza
Evolution, Twilio ou um canal web: implemente somente o provider aprovado para o ambiente.
Fake de teste implementa a mesma porta e não registra rota pública de produção.

| Peça | Mora | Não mora |
|------|------|----------|
| Porta | `messaging-gateway/core/ports/` | agente, casos, UI |
| Adapter Evolution / Twilio | `adapters/<provider>/` | domínio |
| Env | `.env.example` + composition | `getenv` no adapter |

Vocabulário **proibido** fora do adapter: `remoteJid`, `MessageSid`, `content_sid`, `From`, `apikey` de provider.

## Como acrescentar um integrador

1. Pasta `adapters/<provider>/` com `webhook.py` (normalize + auth) e `outbound.py` (`send`).
2. Nomes de env do **provider** (`EVOLUTION_*`, `TWILIO_*`), não da marca do produto.
3. Testes de contrato: 401, envelope neutro, `send` posta o payload, timeout.
4. Registrar no composition. Não crie segunda porta.

## Evolution (sessão)

API de sessão (não WABA). Serve coleta reativa. **Não** substitui template pré-aprovado nem janela oficial da Meta.

Inbound: `POST /api/v1/webhooks/evolution`, header `apikey` timing-safe. Evento `messages.upsert`. `remoteJid` → dígitos (`sender_key`). Texto: `conversation` ou `extendedTextMessage.text`. `fromMe: true` não entra no turno.

Outbound:

```
POST {EVOLUTION_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE}
Header: apikey
JSON: {"number": "<dígitos sem +>", "text": "<já passou na guarda de saída>"}
```

Env: `EVOLUTION_BASE_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`, `EVOLUTION_TIMEOUT_SECONDS`.

## Twilio (WABA)

API oficial: identidade `From` / BSUID, `Body`, `MessageSid`, `X-Twilio-Signature` (HMAC-SHA1 na URL + params ordenados). Timeout no envio. Template pré-aprovado e janela de 24h **só** neste adapter — nunca no agente.

Env: `TWILIO_AUTH_TOKEN`, e quando o outbound existir: `TWILIO_ACCOUNT_SID`, `TWILIO_WHATSAPP_FROM`, timeout.

Inbound hoje: form-urlencoded, 401 se a assinatura falhar. Outbound: Messages API / content SID; o contrato da porta continua `send(destination, text)`.

## Invariantes (todos os adapters)

- Intenção de envio registrada **antes** do HTTP (outbox / append).
- Texto outbound já passou na guarda de saída do agente.
- Identidade de canal opaca; o caso não guarda telefone.
- Sem cliente-deus, sem registry global mutável, sem circuit breaker no mesmo arquivo que o POST até haver segundo caso concreto.

## Conferência

- [ ] Uma porta; N adapters; composition escolhe
- [ ] Somente providers/canais aprovados no requisito/ADR; fake não cria superfície pública
- [ ] Domínio sem `remoteJid` / `MessageSid` / `content_sid`
- [ ] Evolution e/ou Twilio com normalize + `send` + testes de 401 e envelope
- [ ] Env no `.env.example`; adapter sem `getenv`
- [ ] Template/janela Meta só no adapter Twilio
- [ ] `fromMe` / eco do próprio envio não gera turno
