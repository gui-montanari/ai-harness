# Casca de chat

Propriedades do thread. Widget que mistura fetch, HITL e SSE no primitivo é defeito, não modelo.

## O que o primitivo faz

| Peça | Onde |
|------|------|
| Lista de conversas | `ConversationsSidebar.tsx` — burra; items/activeId/onSelect/onNew pela página |
| Auto-resize, Enter/Shift+Enter | `ChatInput.tsx` |
| Avatar + meta | `MessageBubble.tsx` |
| Dots + “Pensando…” rotativo | `thinkingPhrases` no thread; frases na página |
| Opening | página injeta bolha assistant na conversa vazia |
| Header + título da conversa | `ConversationThread` recebe `title` da página |
| Auto-scroll rAF | thread |
| Cursor de streaming | `message.streaming`; a página gera o delta |
| Teto | `LimitReached` — copy pela página |
| Cores | `--chat-*` do tenant |

## Lista (esquerda)

Coluna flex: cabeça (Novo chat + busca) / lista (`flex: 1; min-height: 0; overflow-y`) / footer. Item uma linha, ellipsis, `title` nativo no hover. Ativo: `--action`. Scroll a &lt;120px do fundo → `onLoadMore`. Drawer &lt;900px.

Footer: `UserMenu` (`frontend-shell`) **somente** quando esta lista é o chrome esquerdo da superfície. Dropdown abre **para cima** (`bottom: calc(100% + 8px)`).

Não entra no primitivo: SSE, HITL, launcher, markdown/GFM, typewriter, fetch (typewriter/markdown só na página se o produto for assistente de texto livre).

## Composer

Um form arredondado. `focus-within` = anel `--chat-accent`. Textarea `outline/box-shadow: none` no foco (o `:focus-visible` global senão desenha um retângulo feio). Botão 34px, desabilitado sem texto ou se `busy`. Depois de `busy` false, `focus()` de novo.

## Thinking

Enquanto `busy`: bolha assistant com 3 dots e um rótulo. Se `thinkingPhrases.length > 1`, troca a cada 2.5s sem repetir o índice atual. `role="status"`. Header troca para `busyStatusLabel` e o ponto pulsa.

Não inventar fase `reviewing` sem requisito. Uma lista de frases basta.

## Bolha

Usuário `row-reverse`. `max-width: 78%` (86% no mobile). `white-space: pre-wrap`. Sem justify forçado se o texto for curto. Streaming: `::after` com `▋`. Coleta estruturada: texto plano, sem GFM.

## Host (não quebrar no telefone)

`.sc-root` é `display: flex; flex-direction: column; height: 100%; min-height: 0`. `.sc-messages` leva `flex: 1; min-height: 0; overflow-y: auto`. Composer não cresce. No host página, o pai tem altura explícita; no host tela cheia, o pai é `100dvh` (não `100vh`). Painel flutuante: `max-width: calc(100vw - 32px); max-height: calc(100dvh - 48px)`; abaixo de ~700px vira `100dvh × 100vw`.

Teclado virtual: se `window.visualViewport` existir e o composer ficar coberto, o host alinha a altura ao `visualViewport.height`. Safe area: padding inferior `env(safe-area-inset-bottom)`.

Scrollbar do histórico usa `scrollbar-color: var(--chat-border) transparent` — segue o tema.

## Acessibilidade

Lista `aria-live="polite"` + `aria-busy`. Erro `role="alert"`. Thinking `role="status"`. Hint no `title` do send e visível abaixo. `prefers-reduced-motion` já zera animação no shell. Send ≥ 44px de toque em viewport estreita.

## Página dona

Optimistic user bubble **antes** do await. `busy=true` no POST. Opening só enquanto o histórico é a mensagem inicial. Dados de protocolo/caso **fora** do thread. `lib/api.ts` é o único `fetch`.
