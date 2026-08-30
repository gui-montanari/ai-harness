# Design system — gosto de desenhar

Referência da skill `frontend-surfaces`. Propriedades, não HTML. Paleta e voz vêm do tenant; a gramática é estável.

## Assinatura

Uma coisa memorável por produto. Na Tenda: **fita zebrada de obra + grid de prancheta**. Não é o roxo/ciano do Autodin nem o azul ChatGPT do Stockfy.

| Eixo | Escolha |
|------|---------|
| Display | `Archivo` — titulação de canteiro, tracking negativo |
| Corpo | `IBM Plex Sans` |
| Eyebrow / índice | `IBM Plex Mono`, uppercase, letter-spacing `.1em` |
| Acento itálico no H1 | `Source Serif 4` na cor `--action` |
| Ação | laranja de obra `--action` (`#e4572e` no tenant Tenda) |
| Fundo público | concreto/creme `--bg` |
| Fundo interno | cockpit escuro |

Número 01/02/03 só quando a ordem carrega informação (jornada). Hover com `translateY` pequeno; `prefers-reduced-motion` zera animação.

## Tokens

`html[data-tenant][data-surface]` define `--bg --surface --surface-soft --ink --muted --border --grid --action --ok --danger --tape-a --tape-b`.

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

## Home pública (propriedades do Autodin)

Header sticky com blur, brand-mark + wordmark, nav muted, idioma, CTA primário, fita no topo.

Hero full-bleed, min-height ~680px, grid de prancheta, glow da `--action`, duas colunas: tese + visual do produto. Eyebrow com traço. H1 grande com *uma* palavra em itálico. Lead ~60ch. Dois botões (primário + ghost). Nota com pulso honesto.

Faixa de métricas full-bleed, 3 colunas, valor grande na `--action`, hairline entre elas.

Seção: `padding-block: 7rem`. `section-head` (eyebrow + h2 + lead, max 760px). `feature-grid` 3 cards, `min-height: 270px`, índice mono, ícone quadrado, hover sobe.

CTA-band com gradient suave da `--action`, h2 grande, botão à direita.

Footer curto: legal + links. Páginas internas: `page-main` com título editorial, sem card genérico envolvendo o H1.

```
[ fita ]
[ brand | nav | lang | CTA ]
[ hero 2-col + visual ]
[ métrica | métrica | métrica ]
[ eyebrow / h2 / lead ]
[ card ] [ card ] [ card ]
[ CTA-band ]
[ footer ]
```

Não copiar: paleta roxa, órbitas de carreira, planos, signup, LinkedIn, `Manrope`/`Inter` como voz do produto.

## Chat

Tokens `--chat-*` neste arquivo. Casca, thinking, composer e o que não copiar do stockfy: skill `frontend-chat`.

## Mobile

Hero vira 1 coluna. Métricas empilham. Cards 1 coluna <640px. Nav do header envolve, não some. Chat ocupa a largura.

## Red flags

- Hero dentro de `site-shell` ou de um card escuro
- Chat verde / input `type=text` de uma linha
- Hex de Autodin (`#6c4df6`) ou Stockfy (`#2563eb`) na Tenda
- `ConversationThread` chamando `/api/v1`
- Segunda paleta de chat além dos aliases `--chat-*`
