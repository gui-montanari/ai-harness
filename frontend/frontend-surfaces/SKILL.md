---
name: frontend-surfaces
description: >
  Use when scaffolding or refactoring a React frontend, splitting public vs
  authenticated shells, adding i18n PT/EN, dark/light theme, tenant visual
  tokens, shared UI primitives (PublicHeader, PublicFooter, ThemeToggle,
  LanguageSwitch), designing the unauthenticated area or public home (hero,
  orbit diagram, circular nodes that scale on hover, product board, metric
  strip, sections, CTA), making a layout work on mobile/tablet/desktop, or
  when the user mentions design system, system-visual, visual-node, or
  /frontend-surfaces. For product chat use frontend-chat. For login use
  frontend-login. For logged-in shell use frontend-shell.
---

# Superfícies frontend

SSOT das regras: constituição `AGENTS.md` §3. Este skill é o **lugar** dos arquivos. Não copie HTML, CSS, rotas, auth ou domínio de outro produto.

Gramática visual e tokens: `references/design-system.md` — área não autenticada, tema claro/escuro, PT/EN, viewport, home, visual reativo. Login: `frontend-login`. Área logada: `frontend-shell`. Chat: `frontend-chat`.

## Árvore canônica

```
frontend/
  ui/                         # só com 2+ consumidores reais
    src/
      tokens.css              # tokens semânticos + aliases --chat-*
      public.css              # área pública (header, hero, visual, seções, CTA, footer)
      chat/                   # ConversationThread — skill frontend-chat
      shell.css               # botões, campos, skip-link, site-shell
      tenants/<id>.css        # light + dark por superfície
      i18n/                   # pt-BR + en, mesmas chaves
      components/             # PublicHeader, PublicFooter, LanguageSwitch, ThemeToggle
      theme/                  # TenantProvider + ThemeProvider; zero fetch, zero domínio
  <app>/                      # web-public | backoffice
    src/
      app/App.tsx             # composição
      pages/                  # uma jornada por arquivo
      lib/api.ts              # único lugar de fetch
      layouts/                # se o shell for específico da superfície
```

## Contratos

- `ui/` não importa `/api/v1`, `fetch`, protocolo, caso, SLA, papel.
- Superfície pública e backoffice **não** compartilham sessão, cookie, cache, CSP.
- Sem diretório `portal-user` no v1.
- Tenant visual: `data-tenant` + arquivo em `tenants/`. O front **não** envia `tenant_id` para autorizar.
- Idioma: dicionário `pt-BR` e `en` desde o primeiro commit. `LanguageSwitch` re-renderiza de verdade. Textos canônicos de produto continuam em `docs/requisitos.md`.
- Tema: `data-theme=light|dark` no `html` desde o primeiro commit. Ícone no header público; item do `UserMenu` na área logada. Tudo herda tokens — chat, login, shell inclusos.
- Área pública, shell autenticado, chat, estados vazios/erro, mobile/tablet/desktop e i18n seguem a gramática deste skill. Não copiar implementação, paleta, rotas, HITL, SSE ou domínio de outro produto.
- Hex só em `tokens.css` / `tenants/<id>.css` (os dois temas). Página e componente usam `var(--token)`.
- Home pública é full-bleed. `site-shell` envolve o conteúdo interno, não o hero nem a faixa de métricas.
- Hero tem **um** visual reativo (órbita com nós que escalam no hover, **ou** quadro de jornada). CSS, 180ms. `prefers-reduced-motion` zera movimento.
- Chat: skill `frontend-chat`. Lista à esquerda + thread; primitivos em `ui/src/chat/`; a página dona o fetch.

## Achados

- `App.tsx` god-file com páginas, fetch e CSS
- hex espalhado nas páginas em vez de token
- `ui/` com regra de negócio
- uma SPA para público e interno
- i18n só em um idioma, ou select que não troca o texto
- tema só na home; hex `#fff` no componente
- pasta `models/`/`services/` no frontend com domínio de caso
- hero em card escuro no lugar da gramática de seções
- visual do hero estático (círculo sem `scale` no hover, card sem `translateY`)
- labels ou paleta de outro produto no diagrama em órbita
- chat com input de uma linha, sem header, avatar, auto-resize ou Enter/Shift+Enter
- copiar HTML/CSS de outro produto (paleta, typeface, hex de chat, SSE, markdown)

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Tokens só em `tokens.css` / `tenants/<id>.css`; páginas usam `var(--token)`
- [ ] `data-theme` light **e** dark nas duas superfícies; ícone no header público
- [ ] PT/EN com as mesmas chaves; `LanguageSwitch` re-renderiza de verdade
- [ ] Home: hero 2 col + visual reativo; `site-shell` não envolve o bleed
- [ ] Viewport 375 / 768 / 1280; `dvh`; header não esconde idioma/tema/CTA
- [ ] Público e interno sem sessão/cookie/CSP cruzados
- [ ] Empty / loading / erro / 403 existem e estão traduzidos
- [ ] `ui/` sem `fetch` nem domínio
