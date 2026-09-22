---
description: Atividade parte da produção mais recente em worktree isolada; entrega por cherry-pick e PR green.
alwaysApply: true
---

# Atividade a partir da produção

Vale em todo projeto e todo host. HOW: skill `git-activity`. Nome local (versão, data, prefixo): `AGENTS.md` do produto.

- **De onde partir e o nome.** Skill `git-activity`. Sem branch citada neste turno: worktree nova em `/not-delivery`, a partir de `origin/master` ou `origin/main`. Branch citada em `/not-delivery` ou `/delivered-dev`: seguir essa branch. Não entrar numa dessas que ele não nomeou. Nunca de `develop` nem de checkout sujo. Não desenvolver em `main`/`master`/`develop`. Pasta `{YYYYMMDD}-{HHmm}-{kind}-{slug}` (`{repo}` no nome se `worktrees/` for compartilhada), salvo o produto especializar. O segmento vira `/delivered-dev` quando os commits estão no ref de dev do cliente, e `/delivered` quando estão no ref de produção. O PR `delivery/…` não troca o segmento.
- **Não misturar develop.** `develop` (se existir) é destino de entrega, não base. Sem merge/rebase de develop na branch da atividade.
- **Entrega = cherry-pick.** Branch `delivery/…` a partir da produção atualizada; os mesmos commits em outra `delivery/…` a partir de `origin/develop` quando essa branch existir. Worktree de delivery é **efêmera**: some depois do `gh pr create`. Conflitos resolvidos em cada base. Gates de novo em cada entrega.
- **PR por destino + índice.** Acompanhar checks. Sem check ≠ green. Reconciliar `{worktrees}/ATIVIDADES.md` (`status.py`). Pronto sem URL de PR = não está pronto. Depois do merge, `status.py --prune`: pasta `mergeada` some do disco (controle de encerrada). Agente **não** faz merge nem deploy.

Commit, push e segredo: rule `git-discipline`.
