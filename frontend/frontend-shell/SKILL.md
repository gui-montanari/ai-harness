---
name: frontend-shell
description: >
  Use when building an authenticated app shell: left sidebar, collapsible
  nav, topbar, user avatar dropdown, section menus, or logged-in layout.
  Triggers include AppSidebar, UserMenu, su-sidebar, cockpit, or /frontend-shell.
---

# Shell autenticado

Área logada: **sidebar à esquerda + conteúdo**. Tokens do tenant (`frontend-surfaces`). Sem domínio, sem `fetch` no `ui/`.

Componentes: `AppShell`, `AppSidebar`, `UserMenu`. A página monta items de nav e o logout via `lib/api.ts`.

## Estrutura

```
[ sidebar 260px | topbar + main ]
  brand/logo        título da página
  nav seções        conteúdo (card)
  spacer
  UserMenu (footer)
```

Sidebar e topbar compartilham o **mesmo** fundo de chrome (`--surface` / `--bg` interno). Sem divisória pesada. Conteúdo em card: radius 12–16px, borda suave, não branco puro no claro nem preto puro no escuro.

## Sidebar

- Largura 260px; recolhida **52px** (só ícones). Toggle no logo/brand.
- Brand: mark 40px radius 10px + wordmark. Recolhida: mark; hover no mark revela o toggle.
- Nav: lista vertical. Item com ícone stroke 18px + label. Hover: fundo suave + cor `--action`. Ativo: `--action`, peso 600.
- Seção com chevron: expande filhos; header da seção também pode ser ativo.
- Footer da sidebar: `UserMenu`, não um botão solto no topbar (o topbar fica limpo).
- Mobile (<900px): drawer off-canvas, overlay blur, botão menu no topbar.

## UserMenu / dropdown

- Botão: avatar circular (inicial) + nome. `aria-haspopup="menu"` / `aria-expanded`.
- Dropdown: painel 200px+, radius 11px, borda `--border`, sombra, padding 6px. Fecha no clique fora.
- Itens: ícone 16px + label, hover fundo `--surface-soft`, padding 8px, largura 100%.
- Divisor 1px antes de Sair. Sair em tom `--danger`.
- Tema claro/escuro pode ser item do menu (ícone sol/lua), não um terceiro chrome.

Selects e date pickers do conteúdo repetem o mesmo dropdown (mesma borda, mesmo hover). Um só vocabulário.

## Tokens

Classes de chrome usam `--bg`, `--surface`, `--ink`, `--muted`, `--border`, `--action`. Tema `data-surface="internal"`. Sem hex de outro produto.

## Red flags

- Sidebar à direita “porque o chat é o centro”
- Nav só com texto, sem ícone, ou ícone bitmap pesado
- Dropdown nativo `<select>` cinza no cockpit
- User menu no topbar **e** na sidebar (dois donos)
- Sessão do shell vazando para a home pública (`auth`)
