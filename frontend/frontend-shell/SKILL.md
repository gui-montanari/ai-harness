---
name: frontend-shell
description: >
  Use when building an authenticated app shell: left sidebar, collapsible
  nav, topbar, user avatar dropdown, section menus, or logged-in layout.
  Triggers include AppSidebar, UserMenu, su-sidebar, cockpit, theme in the
  user dropdown, or /frontend-shell.
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
- Footer da sidebar (**sul**): `UserMenu`. `flex` na sidebar + `spacer` (`flex: 1`) empurra o usuário para baixo. Não um botão solto no topbar.
- Recolhida: o footer mostra só o avatar 32px; o nome some. Clique no avatar ainda abre o menu.
- Mobile (<900px): drawer off-canvas, overlay blur, botão menu no topbar. Escape fecha.

## UserMenu / dropdown (sul)

O mesmo componente na sidebar do app **e** na lista de conversas quando o chat é o shell. Um dono.

- Botão largura 100%: avatar circular 32px (inicial, fundo `--action`, texto branco) + nome ellipsis peso 500. Hover: `--surface-soft`. `aria-haspopup="menu"` / `aria-expanded`.
- Dropdown **abre para cima** (`bottom: calc(100% + 8px)`), inset 4px, radius 11–12, borda `--border`, sombra, padding 6px, animação curta 180ms. Fecha no clique fora e no Escape.
- Ordem: tema (sol/lua + `t("themeLight")`/`t("themeDark")`) → itens (config, ajuda) → divisor 1px → Sair em `--danger`.
- Itens: ícone stroke 16px muted + label, padding 8px, hover `--surface-soft`, largura 100%.
- Sem segundo botão de tema no topbar. `html[data-theme]` já pintou; o item só troca a preferência.

Selects e date pickers do conteúdo repetem o mesmo dropdown (mesma borda, mesmo hover). Um só vocabulário.

## Tokens

Classes de chrome usam `--bg`, `--surface`, `--ink`, `--muted`, `--border`, `--action`. Superfície `data-surface="internal"` **e** tema `data-theme`. Sem hex. O cockpit tem light e dark — não é “interno = sempre escuro”.

Idioma: o mesmo `LanguageSwitch` da área pública, no topbar (compacto). PT/EN desde o primeiro commit; strings do shell no dicionário.

## Red flags

- Sidebar à direita “porque o chat é o centro”
- Nav só com texto, sem ícone, ou ícone bitmap pesado
- Dropdown nativo `<select>` cinza no cockpit
- User menu no topbar **e** na sidebar (dois donos)
- Sessão do shell vazando para a home pública (`auth`)
- Tema no topbar **e** no dropdown (dois donos)
- Shell só em um tema; `background: #111` no aside
- UserMenu no topo da sidebar ou dropdown abrindo para baixo e saindo da viewport

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Sidebar esquerda 260 / recolhida 52; nav com ícone stroke
- [ ] UserMenu no **sul** (spacer + footer); dropdown abre para cima
- [ ] Tema é item do menu; idioma no topbar; i18n PT/EN
- [ ] Light **e** dark no cockpit; só `var(--token)`
- [ ] Mobile &lt;900: drawer + overlay + Escape
- [ ] Um UserMenu (não no topbar e na sidebar)
- [ ] Zero `fetch` no `ui/`
