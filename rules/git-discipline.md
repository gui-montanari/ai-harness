---
description: Commit e push só a pedido do humano; nunca pular hook nem versionar segredo.
alwaysApply: true
---

# Disciplina de git

Vale em todo projeto e todo host.

- **Commit** só quando o humano pedir **neste** turno. Diff não pedido não vira commit.
- **Push** só quando o humano pedir. `main`/`master` de repo compartilhado: nunca force push.
- **Não** pular hook (`--no-verify`, `--no-gpg-sign`) salvo o humano pedir explicitamente.
- **Não** versionar segredo: `.env` (exceto `*.example`), `credentials.json`, chaves, tokens.
- Overlay de cliente (autorização de repo alheio, allowlist) **não** entra no harness público. Vive no `{cliente}-harness` (skill `client-harness`).
- Worktree, base de produção, cherry-pick e PR: rule e skill `git-activity`.
