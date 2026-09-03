---
description: Atividade parte da produção mais recente em worktree isolada; entrega por cherry-pick e PR green.
alwaysApply: true
---

# Atividade a partir da produção

Vale em todo projeto e todo host. HOW: skill `git-activity`. Nome local (versão, data, prefixo): `AGENTS.md` do produto.

- **Base = produção.** `git fetch` e worktree/branch a partir de `origin/master` ou `origin/main` (o que o repo usa em produção). Nunca de `develop`, de checkout sujo, nem de branch de entrega antiga.
- **Worktree isolada.** Não desenvolver em `main`/`master`/`develop`. Uma worktree por atividade. Nome: `{kind}/{version}-{slug}` (`feature` ou `bugfix`), salvo o produto especializar.
- **Não misturar develop.** `develop` (se existir) é destino de entrega, não base. Sem merge/rebase de develop na branch da atividade.
- **Entrega = cherry-pick.** Branch `delivery/…` a partir da produção atualizada; os mesmos commits em outra `delivery/…` a partir de `origin/develop` quando essa branch existir. Conflitos resolvidos em cada base. Gates de novo em cada entrega.
- **PR por destino.** Acompanhar checks. Sem check ≠ green. Agente **não** faz merge nem deploy.

Commit, push e segredo: rule `git-discipline`.
