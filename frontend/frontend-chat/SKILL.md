---
name: frontend-chat
description: >
  Use when creating or refactoring a product chat, conversation list,
  conversation thread, ChatGPT-style composer, thinking/busy indicator, auto
  title, conversation limits, a chat that must work on mobile/tablet/desktop,
  a widget panel vs page vs shell host, or when the user mentions
  MessageBubble, ChatInput, ConversationThread, ConversationsSidebar, 100dvh,
  or /frontend-chat.
---

# Chat de produto

SSOT visual: tokens do tenant em `frontend-surfaces`. Este skill é **como montar o produto de chat**. Não copie HTML, CSS, SSE, HITL, fetch ou paleta de outro produto.

Nasce com **lista à esquerda + thread à direita**. Cada conversa tem o próprio histórico. Runtime (SSE, HITL, markdown) fica na página só se o requisito pedir.

Exceção: um único thread sem “novo chat” (ex.: acompanhamento por token). Aí a lista some. Dois ou mais chats = lista obrigatória.

Fila de **tickets** do suporte/operação: skill `frontend-backoffice`, não esta lista.

## Árvore canônica

```
frontend/ui/src/chat/                 # primitivos, zero fetch
  types.ts                            # ChatMessage, ConversationSummary
  MessageBubble.tsx
  ChatInput.tsx
  ConversationThread.tsx              # header + lista + thinking + composer
  ConversationsSidebar.tsx            # lista à esquerda; UserMenu no sul
  LimitReached.tsx                    # modal de teto (copy pela página)
  chat.css                            # só var(--chat-*)
  index.ts
frontend/<app>/src/pages/             # dona do fetch, i18n, opening, busy, título
  lib/api.ts
```

`ConversationThread` e `ConversationsSidebar` são burros. A página: lista, `activeId`, mensagens da conversa ativa, `busy`, thinking, opening, erro, POST, novo chat, teto.

## Quadro

```
[ ConversationsSidebar ~260 | ConversationThread ]
  Novo chat                     header (título da conversa ativa)
  busca                         mensagens deste id
  Recentes                      thinking
    Nova conversa               composer
    Título gerado
  spacer
  UserMenu (sul)                — só se o chat FOR o shell
```

Dois encaixes:

| Onde o chat mora | Lista de conversas | UserMenu |
|------------------|--------------------|----------|
| Superfície inteira (assistente) | é a sidebar esquerda | **sul dessa lista** (`frontend-shell`) |
| Página dentro de `AppShell` | segunda coluna, sem UserMenu | o shell já tem o usuário no sul |

Dois UserMenu = achado.

## Lista de conversas

Primitivo `ConversationsSidebar`. Fetch na página.

- Largura ~260; recolhida 52px (ícone “novo”). Desktop: toggle. &lt;900px: drawer + overlay, botão no header do thread.
- Cabeça: botão **Novo chat** (primário da lista) + busca local pelo título.
- Seção “Recentes” com chevron. Item: título, uma linha, ellipsis. Ativo: fundo `--surface-soft` + `--action`.
- Empty: “Nenhuma conversa”. Paginação: scroll perto do fundo dispara `onLoadMore`.
- Trocar de item: a página troca `activeId` e carrega **só** aquele histórico. Um `ConversationThread`. Estado de composer/busy é por conversa (não vaza thinking da anterior).
- Tokens `--chat-*`. i18n na página.

## Thread

Uma conversa = um `id` + lista de `ChatMessage`. Abrir outra zera o quadro e pinta o histórico dela. Opening só na conversa vazia/nova.

| Propriedade | Como |
|-------------|------|
| Header | avatar + **título da conversa ativa** + status |
| Bolhas | assistente esquerda, usuário direita, avatar 28px |
| Composer | textarea auto-resize (teto 160px), Enter envia, Shift+Enter quebra |
| Foco | um anel no **form** arredondado; textarea sem box-shadow retangular |
| Auto-scroll | `requestAnimationFrame` no histórico |
| Busy | input locked, bolha com dots + rótulo rotativo 2.5s (i18n) |
| Erro | `role="alert"`; some ao digitar de novo |
| Pós-envio | refocus quando `busy` volta a false |

## Título

Começa `null` → a lista mostra “Nova conversa”. Depois da **primeira** resposta do assistente o **servidor** gera um título curto (3–6 palavras, ≤60 caracteres, idioma da UI, sem aspas/emoji/JSON). A página atualiza o item e o header. Falha de título não quebra o turno: permanece “Nova conversa”.

Não gerar título no browser. Use case no serviço de conversas. Não reescrever se o usuário já renomeou.

## Limites

Teto de conversas é **servidor**. Criar além do teto: erro tipado (`conversation_limit_reached`, `limit`, `scope`). A página abre `LimitReached` (título, mensagem com N, hint, fechar). As conversas já abertas continuam. Não esconda a lista. Copy i18n.

## Host e viewport

O primitivo **preenche o pai** (`height: 100%; min-height: 0`).

| Host | Desktop (>900) | Tablet (640–900) | Mobile (&lt;640 / painel &lt;700) |
|------|----------------|------------------|----------------------------------|
| Página / canal | lista + thread | lista drawer | `100dvh`, lista overlay |
| Widget / painel | ~640×680 | encolhe | `100dvh × 100vw` |
| Shell autenticado | o que sobra | drawer | `100dvh` |

- Flex: header / mensagens (`flex: 1; overflow-y: auto; min-height: 0`) / composer.
- `100dvh`, nunca `100vh`. Teclado: `visualViewport`. Bolha 78% / 86%. Send ≥ 44px no toque.

## O que NÃO entra no `ui/`

Fetch, bearer, SSE, HITL, markdown/GFM, typewriter, segundo runtime, hex, regra de teto, geração de título.

## Tempo real

A lista e o thread precisam acompanhar o servidor enquanto a pessoa olha a tela. O **transporte** (SSE ou WebSocket) mora na **página**, nunca no primitivo.

Forma canônica — SSE de invalidação:

1. O servidor autentica o stream com a **mesma sessão** da API (`cookie` HttpOnly, same-origin). Bearer na query do `EventSource` é achado.
2. O evento **não carrega conteúdo**. Payload: sequência ou `inbox.changed`. Sem corpo de mensagem, protocolo, PII, token ou relato.
3. A página, ao receber o ping, **refaz** o GET já existente da lista e do thread ativo. Um canal de dados; o stream só avisa que mudou.
4. Authz no servidor (`case:list` / a ação da superfície). 401 fecha o stream. `Cache-Control: no-store`. Keepalive periódico.
5. Um `EventSource` por página. `close()` no unmount. Trocar de conversa **não** abre segundo stream.
6. Proxy de dev sem timeout curto no path do stream (`timeout: 0`). Buffering de proxy (`X-Accel-Buffering: no`) senão o ping chega em lote.
7. WebSocket só se houver mutação **bidirecional no mesmo socket**. Chat ou fila que só escuta usam SSE. Não misture SSE e polling no mesmo recorte.

`ui/` continua burro: recebe `messages` já atualizadas. Copiar o socket da Stockfy ou de outro produto é achado — copia-se a **regra**, não o arquivo.

## Red flags

- Chat sem lista quando o produto tem “novo chat”
- Um único array de mensagens para todas as conversas
- Título gerado no cliente ou eternamente “Chat”
- Teto só na UI; 201 ainda cria
- UserMenu na lista **e** no `AppShell`
- Input `type="text"` de uma linha; dois anéis de foco
- `fetch` em `ui/src/chat`; `100vh`; histórico que não rola
- Chat claro eterno no `data-theme=dark`
- `EventSource` / `WebSocket` em `ui/src/chat`
- Evento de stream com o texto da mensagem, protocolo ou token
- Token de sessão na URL do stream
- Dois sockets, ou SSE **e** polling juntos

Detalhe de casca: `references/ux.md`.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta. Corrija e volte.

- [ ] Lista à esquerda + thread à direita (ou drawer &lt;900px)
- [ ] Cada `id` tem o próprio histórico; trocar de item não mistura mensagens
- [ ] “Novo chat” cria conversa no servidor e abre thread vazio + opening
- [ ] Título: “Nova conversa” → assunto curto após a 1ª resposta do assistente
- [ ] Teto de conversas: erro do servidor + modal; lista antiga usável
- [ ] UserMenu no sul da lista **ou** no shell — um dono
- [ ] Composer: auto-resize, Enter/Shift+Enter, um anel, refocus
- [ ] Thinking, auto-scroll, `role="alert"` no erro
- [ ] `--chat-*` herda tema; i18n PT/EN em chrome/empty/hint/thinking/modal
- [ ] `100dvh` + `min-height: 0`; 375 / 768 / 1280 conferidos
- [ ] Zero `fetch` no `ui/src/chat`
- [ ] Tempo real (se o recorte pedir): SSE na página, ping sem conteúdo, refetch do GET; cookie same-origin; um stream; `close()` no unmount
