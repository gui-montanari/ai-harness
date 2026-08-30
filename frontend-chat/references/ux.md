# Casca de chat — o que copiar do stockfy-ai

Propriedades. O stockfy-ai-web (master) é a referência de **comportamento**. A implementação de lá mistura fetch, HITL e SSE no widget — isso aqui é defeito, não modelo.

## Mapa stockfy → cá

| Lá | Cá | Traz? |
|----|----|-------|
| `ChatInput` auto-resize, Enter/Shift+Enter | `ui/src/chat/ChatInput.tsx` | sim, com labels via props |
| `MessageBubble` avatar + meta | `MessageBubble.tsx` | sim, sem markdown |
| Dots + “Pensando…” rotativo | `thinkingPhrases` no thread | sim; frases na página |
| `OpeningMessage` | página injeta bolha assistant | sim, sem typewriter |
| Header + status | `ConversationThread` | sim |
| Auto-scroll rAF | thread | sim |
| Cursor de streaming | `message.streaming` | prop; página gera delta se houver |
| `--sc-*` azul | `--chat-*` do tenant | traduzir, não copiar hex |
| `useChatSSE`, HITL, sidebar, launcher | — | não no primitivo |
| `ReactMarkdown`, typewriter | — | só página, se o produto for assistente |
| `Chat.tsx` god-file | página + thread | partir |

## Composer

Um form arredondado. `focus-within` = anel `--chat-accent`. Textarea `outline/box-shadow: none` no foco (o `:focus-visible` global senão desenha um retângulo feio). Botão 34px, desabilitado sem texto ou se `busy`. Depois de `busy` false, `focus()` de novo.

## Thinking

Enquanto `busy`: bolha assistant com 3 dots e um rótulo. Se `thinkingPhrases.length > 1`, troca a cada 2.5s sem repetir o índice atual. `role="status"`. Header troca para `busyStatusLabel` e o ponto pulsa.

Não inventar fase `reviewing` sem requisito. Uma lista de frases basta.

## Bolha

Usuário `row-reverse`. `max-width: 78%` (86% no mobile). `white-space: pre-wrap`. Sem justify forçado se o texto for curto. Streaming: `::after` com `▋`. Sem GFM no canal de coleta.

## Acessibilidade

Lista `aria-live="polite"` + `aria-busy`. Erro `role="alert"`. Thinking `role="status"`. Hint no `title` do send e visível abaixo. `prefers-reduced-motion` já zera animação no shell.

## Página dona

Optimistic user bubble **antes** do await. `busy=true` no POST. Opening só enquanto o histórico é a mensagem inicial. Protocolo/token **fora** do thread (card ao lado). `lib/api.ts` é o único `fetch`.
