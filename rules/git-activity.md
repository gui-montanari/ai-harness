---
description: Atividade parte da produção mais recente em worktree isolada; entrega por cherry-pick e PR green.
alwaysApply: true
---

# Atividade a partir da produção

Vale em todo projeto e todo host. HOW: skill `git-activity`. Nome local (versão, data, prefixo): `AGENTS.md` do produto.

- **Base = produção.** `git fetch` e worktree/branch a partir de `origin/master` ou `origin/main` (o que o repo usa em produção). Nunca de `develop`, de checkout sujo, nem de branch de entrega antiga.
- **Uma worktree por atividade.** Não desenvolver em `main`/`master`/`develop`. Reusar a pasta do slug se já existir. Nome: `{kind}/{YYYYMMDD}-{HHmm}-{slug}` e pasta `{YYYYMMDD}-{HHmm}-{kind}-{slug}` (`feature` ou `bugfix`; `{repo}` na pasta se `worktrees/` for compartilhada), salvo o produto especializar.
- **Não misturar develop.** `develop` (se existir) é destino de entrega, não base. Sem merge/rebase de develop na branch da atividade.
- **Entrega = cherry-pick.** Branch `delivery/…` a partir da produção atualizada; os mesmos commits em outra `delivery/…` a partir de `origin/develop` quando essa branch existir. Worktree de delivery é **efêmera**: some depois do `gh pr create`. Conflitos resolvidos em cada base. Gates de novo em cada entrega.
- **PR por destino + índice.** Acompanhar checks. Sem check ≠ green. Reconciliar `{worktrees}/ATIVIDADES.md` (`status.py`). Pronto sem URL de PR = não está pronto. Depois do merge, `status.py --prune`: pasta `mergeada` some do disco (controle de encerrada). Agente **não** faz merge nem deploy.

Commit, push e segredo: rule `git-discipline`.
