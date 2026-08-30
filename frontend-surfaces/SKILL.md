---
name: frontend-surfaces
description: >
  Use when scaffolding or refactoring a React frontend, splitting public vs
  authenticated shells, adding i18n PT/EN, tenant visual tokens, shared UI
  primitives, designing a public home (hero, metric strip, sections, CTA),
  or when the user mentions design system, Autodin visual language,
  or /frontend-surfaces. For product chat use frontend-chat.
---

# Superfícies frontend

SSOT das regras: constituição `AGENTS.md` §3 e ADR-015 do produto. Este skill é o **lugar** dos arquivos. Não copie HTML, CSS, rotas, auth ou domínio de Autodin/Stockfy.

Gramática visual e tokens: `references/design-system.md`. Thread ChatGPT: skill `frontend-chat`.

## Árvore canônica

```
frontend/
  ui/                         # só com 2+ consumidores reais
    src/
      tokens.css              # tokens semânticos + aliases --chat-*
      public.css              # home pública (hero, seções, CTA)
      chat/                   # ConversationThread — skill frontend-chat
      shell.css               # primitives + shell autenticado
      tenants/<id>.css        # um arquivo por tenant
      i18n/                   # pt-BR + en nativos
      components/             # zero fetch, zero domínio
      theme/TenantProvider.tsx
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
- Idioma: dicionário `pt-BR` e `en` desde o primeiro commit de UI. Textos canônicos de produto continuam em `docs/requisitos.md`.
- Autodin/Stockfy: copiar **propriedades** (home pública, shell autenticado, chat ChatGPT, estados vazios/erro, mobile, i18n). Não copiar implementação, paleta, rotas, HITL, SSE ou domínio.
- Hex só em `tokens.css` / `tenants/<id>.css`. Página e componente usam `var(--token)`.
- Home pública é full-bleed. `site-shell` envolve o conteúdo interno, não o hero nem a faixa de métricas.
- Chat: skill `frontend-chat`. Primitivo em `ui/src/chat/`; a página dona o fetch.

## Achados

- `App.tsx` god-file com páginas, fetch e CSS
- hex espalhado nas páginas em vez de token
- `ui/` com regra de negócio
- uma SPA para público e interno
- i18n só em um idioma
- pasta `models/`/`services/` no frontend com domínio de caso
- hero em card escuro no lugar da gramática de seções
- chat com input de uma linha, sem header, avatar, auto-resize ou Enter/Shift+Enter
- copiar HTML/CSS do Autodin (roxo, órbitas, planos) ou do Stockfy (`--sc-accent: #2563eb`, SSE, markdown)
