---
name: git-activity
description: >
  Use when starting a coding activity, opening a worktree, naming a feature or
  bugfix branch, cherry-picking onto master/main and develop, opening delivery
  PRs, or when the user mentions worktree, delivery, /git-activity. Not
  git-discipline (commit/push permission). Not cicd (pipeline files).
---

# Atividade git (produção → worktree → dual delivery)

**REQUIRED BACKGROUND:** rule `git-activity` (o gate). Esta skill é o HOW.
`AGENTS.md` do produto prevalece em nome de branch, pasta de worktree e se existe `develop`.

Não é desenho de produto (`architecture`). Não é permissão de commit (`git-discipline`).

## 1. Descobrir produção e versão

```bash
git fetch origin --prune
git symbolic-ref refs/remotes/origin/HEAD   # fallback: master se existir, senão main
```

Produção = branch default de **release** (`master` ou `main`), nunca `develop`.
Versão: `AGENTS.md` do produto → senão tag em `origin/<produção>` → senão pergunte. Não invente `0.0.1`.

`kind`: `feature` (comportamento novo) ou `bugfix` (correção na versão corrente). Bugfix **não** bump de versão; a próxima feature é que avança (`feature/0.5.1-foo` → `bugfix/0.5.1-bar` → `feature/0.5.2-baz`).

Padrão global, se o produto não especializar:

```
branch:   {kind}/{version}-{slug}
worktree: {repo}-{version}-{slug}
```

Slug: kebab-case curto. Data (`YYYYMMDD`) só se o `AGENTS.md` do produto pedir.

## 2. Abrir a worktree

Já em worktree ligada desta atividade: não crie outra.

Pasta: a que o produto/workspace já usa (`worktrees/`, `.worktrees/` ignorado). Sem diretório declarado: irmão `worktrees/` do clone, ignorado pelo git.

```bash
git fetch origin
git worktree add -b "{kind}/{version}-{slug}" "$WT" origin/<produção>
cd "$WT"
git merge-base --is-ancestor origin/<produção> HEAD   # tem de ser verdadeiro
```

Proibido: `-b … develop`, `origin/develop` como start-point, checkout da default para editar.

Ambiente que já isola o checkout (codespace, sandbox de PR): **não** aninhe worktree; mesma regra de nome e de base.

## 3. Trabalhar

Commits só na branch da atividade, só se o humano pedir (`git-discipline`). Linear. Não mergear `develop` nem `main` “para atualizar”. Se a produção avançou no meio: rebase **só** em `origin/<produção>` se o humano pedir; senão a entrega (passo 4) já parte da produção nova.

## 4. Entregar (dois destinos independentes)

Quando a atividade está green nos gates do produto:

1. `git fetch origin`. Se produção ou develop avançaram, as deliveries nascem **agora** dessas refs, não de um checkpoint antigo.
2. Listar os SHAs da atividade (`git log --reverse origin/<produção>..HEAD`).
3. Produção:

```bash
git worktree add -b "delivery/{version}-{slug}" "$WT_PROD" origin/<produção>
git -C "$WT_PROD" cherry-pick <sha>…
# gates no $WT_PROD
gh pr create --base <produção> --head "delivery/{version}-{slug}"
```

4. Se `origin/develop` existe:

```bash
git worktree add -b "delivery/{version}-{slug}-develop" "$WT_DEV" origin/develop
git -C "$WT_DEV" cherry-pick <sha>…     # conflitos contra develop, nesta árvore
# gates no $WT_DEV
gh pr create --base develop --head "delivery/{version}-{slug}-develop"
```

Sem `develop`: só o PR de produção.

Nunca merge da branch da atividade em `develop`/`master`. Nunca promover develop inteira para produção. Agente **não** clica Merge e **não** faz deploy.

## 5. Green

`gh pr checks` (ou a UI) em **cada** PR. Job ausente, pulado ou `skipped` ≠ green. Entregar ao humano as duas URLs + status. Ele revisa e mergeia.

Multi-repo: o mesmo slug de atividade em cada repo afetado; PRs e cherry-picks **separados**; ordem de merge a que o contrato exigir (em geral produtor antes de consumidor).

## Red flags

- Worktree ou `-b` a partir de `develop`
- Editar em `main`/`master`/`develop`
- Merge/rebase de develop na feature
- Um único PR “para os dois”
- Cherry-pick em cima de delivery antiga
- Merge ou deploy pelo agente
- Force push em `main`/`master` de repo compartilhado

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] `git fetch`; HEAD da atividade é ancestral-descendente de `origin/<produção>` no início
- [ ] Worktree isolada; nome `{kind}/{version}-{slug}` ou o do `AGENTS.md` do produto
- [ ] Zero merge de develop na atividade
- [ ] Delivery de produção por cherry-pick + PR; develop idem se a branch existir
- [ ] Gates reexecutados em cada delivery; checks green (não ausentes)
- [ ] Sem merge/deploy pelo agente
