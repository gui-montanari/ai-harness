---
name: frontend-chat
description: >
  Use when creating or refactoring a product chat, conversation thread,
  ChatGPT-style composer, thinking/busy indicator, or when the user mentions
  MessageBubble, ChatInput, ConversationThread, or /frontend-chat.
---

# Chat de produto

SSOT visual: tokens do tenant em `frontend-surfaces`. Este skill é **como montar o thread**. Não copie HTML, CSS, SSE, HITL, fetch ou paleta de outro produto.

Runtime (SSE, HITL, markdown, sidebar) fica na página só se o requisito pedir.

## Árvore canônica

```
frontend/ui/src/chat/          # primitivo, zero fetch
  types.ts                     # ChatMessage, ChatRole
  MessageBubble.tsx
  ChatInput.tsx
  ConversationThread.tsx       # quadro: header + lista + thinking + composer
  chat.css                     # só var(--chat-*)
  index.ts
frontend/<app>/src/pages/      # dona do fetch, i18n, opening, busy
  lib/api.ts
```

`ConversationThread` é burro. A página: mensagens, `busy`, frases de thinking, opening, erro, POST.

## UX obrigatória

| Propriedade | Como |
|-------------|------|
| Quadro coluna | header / mensagens / composer |
| Header | avatar + título + status (ponto verde pronto, ponto de ação + pulso se busy) |
| Bolhas | assistente esquerda, usuário direita, avatar 28px |
| Opening | primeira bolha assistant, injetada pela página |
| Composer | textarea auto-resize (teto 160px), Enter envia, Shift+Enter quebra |
| Foco | um anel no **form** arredondado; textarea sem box-shadow retangular |
| Hint | “Enter para enviar · Shift+Enter…” |
| Auto-scroll | `requestAnimationFrame` no histórico |
| Busy | input locked, placeholder de espera, bolha com dots + rótulo |
| Thinking | frases rotativas a cada 2.5s, passadas pela página (i18n) |
| Erro | `role="alert"`; some quando o usuário volta a digitar |
| Pós-envio | refocus no textarea quando `busy` volta a false |
| Tokens | `--chat-*` alias de `--action/--surface/--ink`. Sem hex próprio |

## O que NÃO entra no `ui/`

Fetch, bearer, SSE, HITL, sidebar, launcher, markdown/GFM, typewriter, modal de limite, segundo runtime, hex de provider.

Typewriter e markdown só na página, e só se o produto for assistente de texto livre. Canal confidencial / coleta estruturada: texto plano `pre-wrap`.

Streaming: a bolha aceita `message.streaming` (cursor `▋`). Quem gera o delta é a página. Sem SSE no primitivo.

## Contrato do primitivo

```ts
ConversationThread({
  title, statusLabel, busyStatusLabel,
  assistantInitial, userInitial,
  emptyTitle, emptyBody,
  messages, value, onChange, onSend,
  busy, placeholder, busyPlaceholder,
  sendLabel, hint, thinkingPhrases, error,
})
```

`ChatMessage`: `{ id, role: "user" | "assistant", body, at?, streaming? }`.

## Red flags

- Input `type="text"` de uma linha
- Anel de foco no textarea **e** no form
- `fetch` / `/api/v1` dentro de `ui/src/chat`
- God-file de chat com HITL + SSE + markdown no primitivo
- Paleta de chat com hex próprio (use `--chat-accent`)
- Busy sem bolha de thinking
- Strings de UI hardcoded em PT no primitivo (i18n na página)
- God-file de chat com API + bolha + sidebar

Detalhe de casca: `references/ux.md`.
