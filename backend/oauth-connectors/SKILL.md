---
name: oauth-connectors
description: >
  Use when the user mentions MCP OAuth, PKCE, Protected Resource metadata, or
  LLM host login. Canonical skill is auth — um catálogo, vários emissores.
---

# OAuth de conector é um emissor de `auth`

**REQUIRED SUB-SKILL:** `auth`.

Authorization Code + PKCE S256 para host MCP/LLM vive no catálogo da skill `auth` (`auth_source=connector`). Não é um segundo sistema e não mistura com JWT interno nem `client_credentials`.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Li e marquei a conferência de `auth` (emissor `connector`)
- [ ] Não criei um segundo sistema OAuth ao lado do catálogo
