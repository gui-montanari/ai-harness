# Design system

Referência da skill `frontend-surfaces`. Propriedades, não HTML. Paleta e voz vêm do tenant; a gramática é estável.

Área logada: skill `frontend-shell`. Login: skill `frontend-login`. Chat: skill `frontend-chat`. Este arquivo é o SSOT da **área não autenticada** e dos tokens.

## Assinatura

Uma coisa memorável por produto, definida em `tenants/<id>.css`. Não reutilizar paleta, tipo ou marca de outro produto.

| Eixo | Papel |
|------|-------|
| Display | titulação, tracking negativo |
| Corpo | texto corrido |
| Eyebrow / índice | mono, uppercase, letter-spacing `.1em` |
| Acento itálico no H1 | serif na cor `--action` |
| Ação | `--action` do tenant |
| Fundo público | `--bg` do tenant no tema vigente |
| Fundo interno | cockpit (`data-surface="internal"`) no **mesmo** tema |

Número 01/02/03 só quando a ordem carrega informação (jornada).

## Tokens

`html[data-tenant][data-surface][data-theme]` define `--bg --surface --surface-soft --ink --muted --border --grid --action --ok --danger`. Superfície (`public`/`internal`) e tema (`light`/`dark`) são eixos independentes: **os quatro cruzamentos existem** no arquivo do tenant. Componente nenhum escolhe paleta — só `var(--token)`.

Chat **não** tem paleta própria. Alias:

```css
--chat-bg: var(--surface);
--chat-bg-soft: var(--bg);
--chat-bg-user: color-mix(in srgb, var(--action) 16%, var(--surface));
--chat-bg-assistant: var(--bg);
--chat-fg: var(--ink);
--chat-accent: var(--action);
--chat-border: var(--border);
--chat-font: var(--font-body);
```

Tenant novo = arquivo em `tenants/<id>.css` com **light e dark**. Sem hex na página. `color-scheme: light` / `dark` no `html` acompanha `data-theme` (scrollbar, input nativo, date picker).

`site-shell`: `width: min(1180px, calc(100% - 3rem))`. Envolve o miolo, nunca o bleed do hero nem da faixa de métricas.

Aba do browser (`document.title`, texto ao lado do favicon): nome de exibição do tenant (`TENANT_DISPLAY_NAMES` no `TenantProvider`). `<title>` no `index.html` é o mesmo. Página (fila, login, privacidade) não sobrescreve.

## Tema claro / escuro

Nativo, desde o primeiro commit de UI. Tudo herda: home, legal, login, canal, chat, shell, dropdown, empty/error. Um `background: #fff` ou `color: #000` em componente é achado — quebra o dark.

**Onde o controle vive**

| Superfície | Controle |
|------------|----------|
| Não autenticada | ícone no `PublicHeader` (sol/lua ou ◐), **depois** do CTA e do idioma. `aria-pressed`, `aria-label` i18n |
| Autenticada | tema **e** idioma no `UserMenu` (skill `frontend-shell`). Sem topbar de chrome; sem segundo controle no conteúdo |

**Como funciona de verdade**

1. Script bloqueante no `index.html` **antes do CSS**: lê `localStorage` (`ui:theme`) ou `prefers-color-scheme`; seta `dataset.theme`. Sem isso há flash do tema errado.
2. `ThemeProvider` no `ui/` sincroniza `data-theme`, `color-scheme` e o storage. Ouve `storage` (aba irmã) e `matchMedia` até o usuário escolher.
3. Depois da primeira escolha, a escolha **vence** o SO.
4. `--chat-*` são alias: o thread muda sozinho. Sem `[data-theme] .sc-bubble { background: #1f1f1f }`.

Não esconda o ícone no mobile “para caber”. Ele envolve com o idioma e o CTA.

## Idioma PT / EN

Nativo, desde o primeiro commit. Dicionário `pt-BR` e `en` com as **mesmas** chaves (`MessageKey`). Texto canônico de produto continua em `docs/requisitos.md`; chrome, empty, erro, thinking, aria-label e tema vivem no dicionário.

O `LanguageSwitch` **funciona**: troca o locale, `document.documentElement.lang`, `localStorage` (`ui:locale`) e **re-renderiza** toda string. Controle que só muda `lang` e deixa o PT na tela é achado.

Não é `<select>` nativo. É botão + listbox no **mesmo** vocabulário do `UserMenu` (`.menu-pop`, tokens, hover `--surface-soft`, 180ms). Trigger pílula min-height 38px, padding à direita ≥ 1.8rem; caret (`::after` ou `.lang-caret`) com `right` ≥ 10px — seta colada na borda é achado. Pop abre para baixo (`top: calc(100% + 8px)`), Escape e clique fora fecham. Opção ativa na `--action`.

- Nenhuma literal de UI em JSX. `t("chave")`.
- Chave ausente em um idioma = erro de tipo, não fallback silencioso.
- Datas/números: `toLocaleDateString(locale)`.
- Chat: `thinkingPhrases`, hint, empty, erro — todos `t()`.
- Público e interno podem compartilhar a preferência de idioma/tema (UX). Sessão/cookie de auth **não**.

## Área não autenticada

Superfície pública sem conta. Mesmos tokens, mesmos primitivos, mesma casca em **todas** as páginas públicas (home, legal, canal, 404). Sessão, cookie e CSP **não** atravessam para o backoffice.

Primitivos em `ui/src/components/`, zero fetch, hrefs por props:

| Peça | Papel |
|------|-------|
| `PublicHeader` | sticky, skip-link, brand, nav, **CTA**, idioma, tema |
| `PublicFooter` | legal curto + links |
| `LanguageSwitch` | listbox PT/EN; persiste; `html.lang`; `.menu-pop` |
| `ThemeToggle` | ícone sol/lua; persiste; `data-theme` |
| botão | `.btn` primário / `.ghost` em `shell.css` |

Header: sticky `top: 0`, fundo `--bg` a 82% + `backdrop-filter: blur(20px)`, hairline `--border`, `nav-shell` min-height 72px. Brand-mark 34px, radius 11, sombra da `--action`. Nav muted; hover e `is-active` na `--action`. CTA do header compacto (min-height 38px), **depois** o idioma, **depois** o tema. Nav envolve abaixo de 900px — não some, não overflow hidden.

Dev: Vite `server.host: true` (ou bind equivalente em 0.0.0.0 / 127.0.0.1). Escutar só `[::1]` faz o link interno `http://127.0.0.1:<porta>` falhar.

Footer: `padding-block: 2rem`, tipo 0.72rem muted, links com hover `--action`.

Páginas internas (`page-main`): título editorial, lead ~68ch, glow radial discreto da `--action`. Sem card genérico em volta do H1. Formulário de acesso reusa `frontend-login` (duas colunas, card radius 20).

## Home

Página-bandeira da área pública. Full-bleed.

```
[ PublicHeader: brand | nav | CTA | lang | tema ]
[ hero 2-col: tese + visual reativo ]
[ métrica | métrica | métrica ]
[ eyebrow / h2 / lead ]
[ card ] [ card ] [ card ]
[ CTA-band ]
[ PublicFooter ]
```

Hero: min-height ~680px, grid 46px, glow radial da `--action` no canto, fade nas laterais com `--bg`. A grade é **fundo**: `--grid-hero` e `--grid-accent` ≤ ~0.10 de opacidade. Laranja forte na malha compete com o H1 e o CTA — o acento `--action` fica no texto e nos botões, não no quadriculado. Grid `1.05fr 0.95fr`, gap 5rem, padding-block 6.5rem. Eyebrow com traço de 18px. H1 `clamp(2.5rem, 5.2vw, 4.4rem)`, tracking `-0.06em`, **uma** palavra em itálico `--action`. Lead ~60ch, 1.75. Dois botões (primário + ghost). Nota com pulso honesto — só afirma o que é verdade.

Faixa de métricas: fundo `--surface`, 3 colunas, valor 1.7rem `--action`, hairline entre elas.

Seção: `padding-block: 7rem`. `section-head` max 760px. `feature-grid` 3 cards, min-height 270px, índice mono, ícone 46px radius 14 na assinatura do tenant.

CTA-band: gradient 135deg `--action` 10% + `--ink` 4% sobre `--surface`, h2 grande, botão à direita.

## Visual do hero

O segundo slot do hero **não é screenshot nem ilustração morta**. É um objeto do produto que reage ao ponteiro. Um visual por home — não os dois.

**A — diagrama em órbita**, quando o produto é um sistema de capacidades ligadas:

- palco quadrado, `aspect-ratio: 1`, max 480px
- grade rotacionada 45°, radius 26px, grid 28px, sombra do token (fica parada)
- duas órbitas concêntricas, só decoração: sólida `inset 13%` gira 30s linear; tracejada `inset 31%` gira 19s no sentido inverso. Borda `color-mix(--action 40%, --border)`
- nós **circulares**, posição absoluta (não andam com a órbita — a órbita é fundo vivo; o nó é o alvo do hover)
- centro maior (`inset ~37%`), satélites 74px nos quatro cantos
- cada nó: `backdrop-filter: blur(12px)`, fundo `--surface` 88%, borda `--border`, sombra da `--action` 12%. Label: span mono ~0.5rem muted + strong display ~0.72rem
- caption mono ~0.58rem no rodapé do palco
- labels e números são **deste** produto, nestes tokens

O detalhe que dá elegância: o círculo responde ao mouse.

```css
.visual-node {
  border-radius: 50%;
  backdrop-filter: blur(12px);
  transition: transform 180ms ease, border-color 180ms ease;
}
.visual-node:hover {
  transform: scale(1.08);
  border-color: var(--action);
}
```

CSS puro. Sem JS, canvas, Lottie ou 3D para este hover.

**B — quadro de jornada**, quando o produto é uma sequência numerada: card de vidro max 420px, radius 18, blur 12px, 01–n em mono `--action`, assinatura do tenant na borda (marca local, não copiada). Hover do card pode ser `translateY(-3px)`; não inventa órbita por cima.

## Microinterações

São a diferença entre layout correto e produto elegante. Todas em CSS, 160–180ms ease, tokens do tenant.

| Onde | Repouso → hover / estado |
|------|--------------------------|
| Nó circular do visual A | `scale(1.08)` + borda `--action` |
| Órbitas | giro lento contínuo (30s / 19s reverse) |
| Feature-card | `translateY(-5px)` + `--shadow` |
| Botão | `translateY(-2px)`; seta `→` `translateX(4px)` |
| Nav-link | cor `--action` |
| Pulso da nota | disco 8px `--ok` + halo 6px na mesma cor |

Botão: min-height 46px, radius ~12, gap 0.55rem, primário `--action` / texto branco, ghost superfície 70% + borda. Um anel de `:focus-visible` (o token `--focus`). Sem segundo retângulo.

`prefers-reduced-motion: reduce` zera `animation` e `transform` de hover. Cor de borda no hover pode permanecer. Scroll `auto`.

Pulso e status só quando o fato é honesto. “Ao vivo” mentiroso é pior que estático.

## Primitivos (sempre token, sempre compartilhados)

Vivem em `ui/src/components/` + `shell.css` quando há **2+ consumidores reais**. Página não copia borda, hover nem hex. Variante de status é **prop** (`ok | action | danger | muted`) que a página mapeia da API — não um regex no rótulo.

| Peça | Papel |
|------|--------|
| `DataTable` | lista operacional (catálogo, fila tabular) |
| `StatusBadge` | pílula de estado |
| `EmptyState` | empty da tabela/lista |
| `Pagination` | página estável (cursor da API) |
| `Flash` | toast `role="status"` |
| campo / botão | já em `frontend-login` / botão acima |

### Tabela

Um vocabulário. Backoffice, catálogo e qualquer listagem usam o mesmo. Inbox de tickets em split (`frontend-backoffice`) é **card**, não tabela — não misture os dois no mesmo recorte.

```
[ heading + ações ]
[ table-scroll ]
    thead sticky
    tbody (hover, foco, clique)
[ Pagination ]
```

- Wrapper `.table-scroll { overflow-x: auto }`. Tabela `width: 100%`, `border-collapse: collapse`. `min-width` só quando as colunas não cabem (não encolhe letra).
- `th`: `scope="col"`, muted, peso 600, 0.6–0.75rem, uppercase + letter-spacing se for índice, fundo `--surface-soft`, nowrap, padding `.75rem 1rem`, hairline `--border`.
- `td`: padding `.85rem 1rem`, `--ink`, vertical-align middle, border-bottom `--border`.
- `tbody tr:hover`: `color-mix(--action 4%, --surface)` ou `--surface-soft`. Linha clicável: `cursor: pointer`, Enter, `:focus-visible` anel `--action` (offset interno). Destaque da linha ativa: `--surface-soft` + acento.
- Número: `font-variant-numeric: tabular-nums`, `text-align: end`. Protocolo/id: `font-mono`, ellipsis, muted, `title` nativo.
- Badge **dentro** da célula usa `StatusBadge`. Sem hex de “verde do status”.
- `thead` pode ser sticky no scroll vertical longo.
- Empty: `EmptyState` no lugar do tbody. Loading: skeleton de 5–8 linhas, não spinner no canto.
- Paginação **abaixo**, i18n, prev/next; página/cursor vêm da API (`ops-backoffice`). Front não fatia o JSON inteiro.
- Mobile/tablet: scroll horizontal no wrapper **ou** cada linha vira card com `data-label` nas células. Não esconda coluna crítica em silêncio. Toque ≥ 44px na linha clicável.
- Sem tabela aninhada, sem `<table>` de layout, sem `border="1"`.

`DataTable({ columns, rows, rowKey, onRowAction? })` é burro. Fetch na página.

### Badge, tabs, flash, toolbar

- **Badge:** pílula radius 999, padding 4px 10px, 0.72rem, peso 700. Fundo `color-mix(token 14–16%, --surface)`, texto no token. Cor + texto.
- **Tabs/chips de filtro:** o mesmo hover/ativo da nav (`--action`, peso 600). Filtro é query de servidor.
- **Flash:** topo do main, `role="status"`, some sozinho ~4s, borda `--ok`/`--danger`. Sem `alert()` nativo.
- **Toolbar:** flex, wrap, gap 8px, alinha à heading da tabela.
- **Divisor:** 1px `--border`.
- **Avatar:** 32px, circular, `--action`, inicial — o do `UserMenu` (`frontend-shell`). Não um segundo.

## Estados (empty / loading / erro)

Toda lista e toda página nasce com os três, i18n, tokens. Sem “tela branca”.

| Estado | Forma |
|--------|--------|
| Empty | borda dashed, texto muted, **uma** ação (CTA). Não um illustration pack. |
| Loading | skeleton no bloco que carrega; chrome (header/sidebar) permanece. Spinner só em ação pontual. |
| Erro | `role="alert"`; mensagem uniforme; retry só se o pedido for idempotente |
| 403 / 404 | página própria, tom editorial, sem stack trace |

Cor não é o único sinal (`--ok` / `--danger` + texto). Verificar empty e erro nos dois temas e nos três viewports.

## Chat

Tokens `--chat-*` neste arquivo. Casca, thinking, composer e **host responsivo**: skill `frontend-chat`.

## Viewport — mobile / tablet / desktop

Nasce nos três. `viewport` = `width=device-width, initial-scale=1`. Altura usa `dvh`, não `vh` (barra e teclado do telefone). `env(safe-area-inset-*)` no header/composer. Alvo de toque ≥ 44px abaixo de 900px. Hover é extra: a ação existe no toque.

| | Largura | O que muda |
|--|---------|------------|
| Mobile | <640px | 1 coluna; métricas empilham; features 1; botões 100%; nav envolve; chat 100dvh |
| Tablet | 640–900px | hero 1 coluna; features 2; form-intro estático; sidebar autenticada vira drawer; chat **não** full-bleed |
| Desktop | >900px | hero 2 col; features 3; sidebar 260; chat preenche o host |

`site-shell` 1180. Header nunca esconde idioma, tema ou CTA atrás de `overflow: hidden`. Verificar 375, 768 e 1280 antes de declarar pronto.

## Red flags

- Hero dentro de `site-shell` ou de um card escuro
- Quadriculado do hero com `--grid-accent` alto (laranja competindo com o texto)
- Visual do hero estático: círculo que não escala, card que não sobe, botão sem seta
- Dois visuais no mesmo hero, ou órbita **e** quadro
- Labels, paleta ou typeface de outro produto no visual
- JS/canvas/Lottie para o hover do nó
- Feature-card sem `min-height` e sem `translateY`
- Sem `prefers-reduced-motion`
- Chat verde / input `type=text` de uma linha
- Hex de outro produto nas páginas
- `ConversationThread` chamando `/api/v1`
- Segunda paleta de chat além dos aliases `--chat-*`
- Header/footer copiados em cada página em vez do primitivo
- Sessão da área logada vazando para a home
- Hex ou `background: #fff` no componente (quebra o dark)
- Tema só na home; login/chat/shell em claro eterno
- `LanguageSwitch` que não re-renderiza as strings
- `LanguageSwitch` com `<select>` nativo; opções cinza do SO; caret colado na borda
- idioma/tema à esquerda do CTA no header público
- Vite de dev só em `[::1]`; `127.0.0.1` recusa conexão
- `document.title` com nome de página (fila, login, backoffice) em vez do tenant
- Dicionário só em PT, ou chave só em um idioma
- Layout só desktop; tablet tratado como “mobile quebrado”
- Chat com `100vh` (teclado cobre o composer)
- Tabela nativa sem token; hex na célula; status por regex no rótulo
- Página reimplementando hover/borda da tabela
- Inbox de ticket **e** tabela para o mesmo recorte
- Paginação no cliente sobre payload completo
