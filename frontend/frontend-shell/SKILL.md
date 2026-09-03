---
name: frontend-shell
description: >
  Use when building an authenticated app shell: left sidebar, collapsible
  nav, user avatar dropdown, section menus, or logged-in layout.
  Triggers include AppSidebar, UserMenu, su-sidebar, cockpit, theme in the
  user dropdown, hamburger/panel toggle, or /frontend-shell.
---

# Shell autenticado

Área logada: **sidebar à esquerda + conteúdo**. Tokens do tenant (`frontend-surfaces`). Sem domínio, sem `fetch` no `ui/`.

Componentes: `AppShell`, `AppSidebar`, `UserMenu`, `SidebarToggleIcon`. A página monta items de nav e o logout via `lib/api.ts`.

## Estrutura

```
[ sidebar 260px | main ]
  brand + toggle      conteúdo (H1 da jornada, cards)
  nav: tópicos
       subtópicos
  spacer
  UserMenu (sul)
```

A sidebar é **chrome fixo no viewport** (`height: 100dvh`, não rola com o main). Hairline `border-right: 1px solid var(--border)` separa o menu do conteúdo. Sem topbar de chrome no bloco central. Conteúdo em card: radius 12–16px, borda suave, não branco puro no claro nem preto puro no escuro.

## Sidebar

- Largura 260px; recolhida **52px** (só ícones). O `UserMenu` permanece no sul nos dois estados.
- A coluna **não** cresce com o main e **não** sai da tela: `flex`/`height: 100dvh` no shell; overflow do documento fica no `main`. Nav longo rola **dentro** da lista; brand e footer ficam.
- Toggle: ícone de **painel** (retângulo + trilho à esquerda — `SidebarToggleIcon`), à direita do brand. Não são três traços no header do conteúdo. Recolhida: hover no mark 40px troca o logo pelo mesmo ícone e o clique expande.
- Brand: mark 40px radius 10px + wordmark. Recolhida: só o mark.
- **Respiro marca → menu:** o bloco do brand não cola no primeiro tópico. Gap ≥ `1.5rem` (`margin-bottom` do brand ou `padding-top` da nav). Recolhida pode ser um pouco menor (~0.85rem). Logo + wordmark + item no mesmo bloco visual é achado.
- **Tipo do menu é chrome, não título.** Tópico: ~13px (`0.81rem`), peso 500, cor `--muted`. Subtópico: igual ou 1px menor (`0.78rem`), indentado. Hierarquia por recuo e peso, não por herdar os 16px do `body`. `font: inherit` no item de nav é achado.
- Nav em **tópicos e subtópicos**. `NavItem.children` opcional. Tópico = header com ícone stroke 18px + label + chevron (visível no hover). Subtópico indentado, sem segundo ícone. Header da seção pode ficar ativo se um filho estiver ativo. Recolhida: o ícone do tópico representa a seção (vai ao filho ativo ou ao primeiro).
- **Um href por folha, token curto de duas letras** nas SPAs. Home pública permanece `/`. Login interno: `/in`. Logado: `/cv`, `/us`, `/ft`, `/pf`. Público: `/pv` privacidade, `/ax` acessibilidade, `/ac` acompanhamento (aliases longos redirecionam). A API continua `/api/v1/…`.
- Não inventar rota, tela ou tópico sem consumidor real. Uma seção com um filho honesto vale mais do que um inventário fantasma.
- Hover do item: fundo suave + cor `--action`. Ativo: `--action`, peso 600.
- Footer da sidebar (**sul**): `UserMenu`, separado por hairline `--border`. Spacer (`flex: 1`) empurra o usuário para baixo. Não um botão solto no conteúdo.
- Recolhida: o footer mostra só o avatar 32px; o nome some. Clique no avatar ainda abre o menu, **ao lado** da coluna (não clipado por `overflow: hidden` na aside inteira).
- Mobile (<900px): drawer off-canvas, overlay blur, botão do mesmo ícone de painel **só** para abrir o drawer. Escape fecha. No drawer o menu aparece expandido (tópico + rótulo + perfil).

## UserMenu / dropdown (sul)

O mesmo componente na sidebar do app **e** na lista de conversas quando o chat é o shell. Um dono.

- Botão largura 100%: avatar circular 32px (inicial, fundo `--action`, texto branco) + nome ellipsis peso 500. Hover: `--surface-soft`. `aria-haspopup="menu"` / `aria-expanded`.
- Dropdown **abre para cima** (`bottom: calc(100% + 8px)`), inset 4px, radius 11–12, borda `--border`, sombra, padding 6px, animação curta 180ms. Fecha no clique fora e no Escape. Recolhida: abre à direita da coluna.
- Ordem: tema (sol/lua + `t("themeLight")`/`t("themeDark")`) → **PT e EN na mesma linha** (par, não dois itens empilhados) → divisor 1px sutil → itens de conta (perfil, futuros) → divisor 1px → Sair em `--danger`.
- O divisor separa o chrome (tema + idioma) das opções de conta. Sem ele, PT/EN misturam com Perfil e o menu perde hierarquia.
- Idioma autenticado **não** é a pílula `LanguageSwitch` do header público. No UserMenu é um **grupo na mesma opção** (`role="group"`, PT|EN, o ativo em `--action`). A pílula listbox fica na área não autenticada (`frontend-surfaces`).
- Itens: ícone stroke 16px muted + label, padding 8px, hover `--surface-soft`, largura 100%.
- Sem segundo controle de tema ou idioma no chrome do conteúdo. `html[data-theme]` já pintou; o item só troca a preferência.

Selects e date pickers do conteúdo repetem o mesmo dropdown (`.menu-pop`, mesma borda, mesmo hover). Um só vocabulário. `LanguageSwitch` **não** é `<select>` nativo — skill `frontend-surfaces`.

## Tokens

Classes de chrome usam `--bg`, `--surface`, `--ink`, `--muted`, `--border`, `--action`. Superfície `data-surface="internal"` **e** tema `data-theme`. Sem hex. O cockpit tem light e dark — não é “interno = sempre escuro”.

Título da **jornada** (fila, caso) é H1 **do conteúdo**, não de um header de chrome. Título da **aba** (`document.title`) é o tenant — skill `frontend-surfaces`. Não copiar o rótulo da fila para a aba.

## Red flags

- Sidebar à direita “porque o chat é o centro”
- Sidebar que rola com a página e leva o perfil embora
- Chrome central com título da jornada + PT + tema
- Item de menu sem path próprio, ou tudo em `/`
- Path REST na barra (`/conversations`) ou sigla inventada (`/hc`, `/helpchat`)
- Nav plana só com um rótulo, sem tópico/subtópico quando o produto já tem seções
- Marca colada no primeiro tópico (gap &lt; 20px)
- Tópico de nav com tipo de H1 / `font: inherit` / 16px / peso 700
- Nav só com texto, sem ícone, ou ícone bitmap pesado
- Hamburger de três traços no topbar do conteúdo no desktop
- Dropdown nativo `<select>` cinza no cockpit
- User menu no topbar **e** na sidebar (dois donos)
- Sessão do shell vazando para a home pública (`auth`)
- Tema ou idioma no conteúdo **e** no dropdown (dois donos)
- Shell só em um tema; `background: #111` no aside
- UserMenu no topo da sidebar ou dropdown abrindo para baixo e saindo da viewport
- `overflow: hidden` na aside inteira clipando o menu do perfil

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Sidebar esquerda 260 / recolhida 52; `100dvh`; não rola com o main
- [ ] Hairline `border-right` entre sidebar e conteúdo; sem topbar de chrome
- [ ] Toggle de painel no brand; mobile só abre o drawer
- [ ] Nav em tópicos/subtópicos (`children`); ícone stroke; cada folha com path próprio
- [ ] Gap marca→menu ≥ 1.5rem; tópico ~13px peso 500 muted, não o tipo do body
- [ ] UserMenu no **sul** (spacer + footer); dropdown abre para cima
- [ ] Tema no menu; PT/EN na **mesma linha**; divisor entre chrome e conta; i18n PT/EN
- [ ] Light **e** dark no cockpit; só `var(--token)`
- [ ] Mobile &lt;900: drawer + overlay + Escape; perfil visível
- [ ] Um UserMenu (não no topbar e na sidebar)
- [ ] Zero `fetch` no `ui/`
