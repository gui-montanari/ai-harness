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
| Fundo público | `--bg` claro do tenant |
| Fundo interno | cockpit (`data-surface="internal"`) |

Número 01/02/03 só quando a ordem carrega informação (jornada).

## Tokens

`html[data-tenant][data-surface]` define `--bg --surface --surface-soft --ink --muted --border --grid --action --ok --danger`.

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

Tenant novo = arquivo em `tenants/<id>.css`. Sem hex na página.

`site-shell`: `width: min(1180px, calc(100% - 3rem))`. Envolve o miolo, nunca o bleed do hero nem da faixa de métricas.

## Área não autenticada

Superfície pública sem conta. Mesmos tokens, mesmos primitivos, mesma casca em **todas** as páginas públicas (home, legal, canal, 404). Sessão, cookie e CSP **não** atravessam para o backoffice.

Primitivos em `ui/src/components/`, zero fetch, hrefs por props:

| Peça | Papel |
|------|-------|
| `PublicHeader` | sticky, skip-link, brand, nav, idioma, CTA |
| `PublicFooter` | legal curto + links |
| botão | `.btn` primário / `.ghost` em `shell.css` |

Header: sticky `top: 0`, fundo `--bg` a 82% + `backdrop-filter: blur(20px)`, hairline `--border`, `nav-shell` min-height 72px. Brand-mark 34px, radius 11, sombra da `--action`. Nav muted; hover e `is-active` na `--action`. CTA do header compacto (min-height 38px). Nav envolve abaixo de 900px — não some, não overflow hidden.

Footer: `padding-block: 2rem`, tipo 0.72rem muted, links com hover `--action`.

Páginas internas (`page-main`): título editorial, lead ~68ch, glow radial discreto da `--action`. Sem card genérico em volta do H1. Formulário de acesso reusa `frontend-login` (duas colunas, card radius 20).

## Home

Página-bandeira da área pública. Full-bleed.

```
[ PublicHeader: brand | nav | lang | CTA ]
[ hero 2-col: tese + visual reativo ]
[ métrica | métrica | métrica ]
[ eyebrow / h2 / lead ]
[ card ] [ card ] [ card ]
[ CTA-band ]
[ PublicFooter ]
```

Hero: min-height ~680px, grid 46px, glow radial da `--action` no canto, fade nas laterais com `--bg`. Grid `1.05fr 0.95fr`, gap 5rem, padding-block 6.5rem. Eyebrow com traço de 18px. H1 `clamp(2.5rem, 5.2vw, 4.4rem)`, tracking `-0.06em`, **uma** palavra em itálico `--action`. Lead ~60ch, 1.75. Dois botões (primário + ghost). Nota com pulso honesto — só afirma o que é verdade.

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

## Chat

Tokens `--chat-*` neste arquivo. Casca, thinking e composer: skill `frontend-chat`.

## Mobile

| Largura | O que muda |
|---------|------------|
| <900px | hero 1 coluna, visual max 430px, features 2 colunas, nav do header envolve, form-intro deixa de ser sticky |
| <640px | métricas empilham (hairline vira bottom), features 1 coluna, botões do hero 100%, seção `padding-block: 5rem`, CTA empilha |

Chat ocupa a largura. Header nunca esconde o CTA atrás de overflow.

## Red flags

- Hero dentro de `site-shell` ou de um card escuro
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
