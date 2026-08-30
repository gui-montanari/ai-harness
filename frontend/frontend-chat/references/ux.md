# Casca de chat

Propriedades do thread. Widget que mistura fetch, HITL e SSE no primitivo é defeito, não modelo.

## O que o primitivo faz

| Peça | Onde |
|------|------|
| Auto-resize, Enter/Shift+Enter | `ui/src/chat/ChatInput.tsx` |
| Avatar + meta | `MessageBubble.tsx` |
| Dots + “Pensando…” rotativo | `thinkingPhrases` no thread; frases na página |
| Opening | página injeta bolha assistant |
| Header + status | `ConversationThread` |
| Auto-scroll rAF | thread |
| Cursor de streaming | `message.streaming`; a página gera o delta |
| Cores | `--chat-*` do tenant |

Não entra no primitivo: SSE, HITL, sidebar, launcher, markdown/GFM, typewriter (typewriter/markdown só na página se o produto for assistente de texto livre).

## Composer

Um form arredondado. `focus-within` = anel `--chat-accent`. Textarea `outline/box-shadow: none` no foco (o `:focus-visible` global senão desenha um retângulo feio). Botão 34px, desabilitado sem texto ou se `busy`. Depois de `busy` false, `focus()` de novo.

## Thinking

Enquanto `busy`: bolha assistant com 3 dots e um rótulo. Se `thinkingPhrases.length > 1`, troca a cada 2.5s sem repetir o índice atual. `role="status"`. Header troca para `busyStatusLabel` e o ponto pulsa.

Não inventar fase `reviewing` sem requisito. Uma lista de frases basta.

## Bolha

Usuário `row-reverse`. `max-width: 78%` (86% no mobile). `white-space: pre-wrap`. Sem justify forçado se o texto for curto. Streaming: `::after` com `▋`. Coleta estruturada: texto plano, sem GFM.

## Acessibilidade

Lista `aria-live="polite"` + `aria-busy`. Erro `role="alert"`. Thinking `role="status"`. Hint no `title` do send e visível abaixo. `prefers-reduced-motion` já zera animação no shell.

## Página dona

Optimistic user bubble **antes** do await. `busy=true` no POST. Opening só enquanto o histórico é a mensagem inicial. Dados de protocolo/caso **fora** do thread. `lib/api.ts` é o único `fetch`.
