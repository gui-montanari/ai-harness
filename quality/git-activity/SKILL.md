---
name: git-activity
description: >
  Use when starting a coding activity, opening a worktree, naming a feature or
  bugfix branch, cherry-picking onto master/main and develop, opening delivery
  PRs, reconciling worktrees/ATIVIDADES.md, or when the user mentions worktree,
  delivery, /git-activity. Not git-discipline (commit/push permission). Not
  cicd (pipeline files).
---

# Atividade git (produção → worktree → dual delivery → índice)

**REQUIRED BACKGROUND:** rule `git-activity` (o gate). Esta skill é o HOW.
`AGENTS.md` do produto prevalece em nome de branch, pasta de worktree e se existe `develop`.

Não é desenho de produto (`architecture`). Não é permissão de commit (`git-discipline`).

Turno ≠ atividade. Uma pasta por recorte; reabrir a que já existe.

## 1. Reusar

```bash
git fetch origin --prune
git worktree list
python3 <SKILL_DIR>/status.py --prune
python3 <SKILL_DIR>/status.py --check-slug "{slug}"
```

Exit 0: `cd` nesse path. **Não** crie outra. Pergunta, plano ou diagnóstico sem patch: nem worktree.

## 2. Nomes

Produção = default de **release** (`master` ou `main`), nunca `develop`.
`kind`: `feature` (comportamento novo) ou `bugfix` (correção na versão corrente). Bugfix **não** bump de versão.

Stamp = relógio do host: `date +%Y%m%d-%H%M`. Slug = kebab-case curto. Versão de produto, se houver, entra **no slug** (`0.5.2-foo`), não no prefixo.

Padrão global, se o produto não especializar:

```
branch:   {kind}/{YYYYMMDD}-{HHmm}-{slug}
pasta:    {YYYYMMDD}-{HHmm}-{kind}-{slug}
```

Diretório de worktrees compartilhado entre repos (irmão do clone, mistura vários produtos):

```
pasta: {YYYYMMDD}-{HHmm}-{repo}-{kind}-{slug}
```

Delivery: `delivery/{YYYYMMDD}-{HHmm}-{slug}` e, se houver develop, o mesmo com sufixo `-develop`.

## 3. Abrir

Pasta: a que o produto/workspace já usa (`worktrees/`, `.worktrees/` ignorado). Sem diretório declarado: irmão `worktrees/` do clone, ignorado pelo git.

```bash
git worktree add -b "{kind}/{YYYYMMDD}-{HHmm}-{slug}" "$WT" origin/<produção>
cd "$WT"
git merge-base --is-ancestor origin/<produção> HEAD   # tem de ser verdadeiro
python3 <SKILL_DIR>/status.py
```

Proibido: `-b … develop`, `origin/develop` como start-point, checkout da default para editar.

Ambiente que já isola o checkout (codespace, sandbox de PR): **não** aninhe worktree; mesma regra de nome e de base.

## 4. Trabalhar

Commits só na branch da atividade, só se o humano pedir (`git-discipline`). Linear. Não mergear `develop` nem `main` “para atualizar”. Se a produção avançou no meio: rebase **só** em `origin/<produção>` se o humano pedir; senão a entrega (passo 5) já parte da produção nova.

## 5. Entregar (dois destinos; delivery efêmera)

Quando a atividade está green nos gates do produto:

1. `git fetch origin`. Se produção ou develop avançaram, as deliveries nascem **agora** dessas refs, não de um checkpoint antigo.
2. Listar os SHAs da atividade (`git log --reverse origin/<produção>..HEAD`).
3. Produção:

```bash
git worktree add -b "delivery/{YYYYMMDD}-{HHmm}-{slug}" "$WT_PROD" origin/<produção>
git -C "$WT_PROD" cherry-pick <sha>…
# gates no $WT_PROD
gh pr create --base <produção> --head "delivery/{YYYYMMDD}-{HHmm}-{slug}"
git worktree remove "$WT_PROD"
```

4. Se `origin/develop` existe: o mesmo com `delivery/{YYYYMMDD}-{HHmm}-{slug}-develop` a partir de `origin/develop`. Conflitos contra develop, nesta árvore. `gh pr create --base develop`. Depois `git worktree remove`.

Sem `develop`: só o PR de produção.

A pasta delivery **some** depois do `gh pr create`. A branch permanece no remoto. A activity fica no disco **só até o merge**.

Nunca merge da branch da atividade em `develop`/`master`. Nunca promover develop inteira para produção. Agente **não** clica Merge e **não** faz deploy.

## 6. Green e índice

`gh pr checks` (ou a UI) em **cada** PR. Job ausente, pulado ou `skipped` ≠ green.

```bash
python3 <SKILL_DIR>/status.py
```

Escreve `{worktrees}/ATIVIDADES.md` (fora do git do produto) a partir de `git worktree list` + `gh pr`. Não editar o markdown à mão. Pronto **sem** URL de PR no índice = não está pronto. Entregar ao humano as URLs + status. Ele revisa e mergeia.

Multi-repo: o mesmo slug de atividade em cada repo afetado; PRs e cherry-picks **separados**; ordem de merge a que o contrato exigir (em geral produtor antes de consumidor).

## 7. Depois do merge — pasta some

O merge no remoto **é** a autorização para limpar o disco. `mergeada` no índice = worktree não deveria existir. Pasta vazia de mergeadas é o controle: se ainda está em `worktrees/`, não foi encerrada.

```bash
git fetch origin --prune
python3 <SKILL_DIR>/status.py --prune
```

Remove só `mergeada`, limpa, sem `--force`. Não toca `aberta` / `pr-aberta`, o clone de produção, nem a pasta em que o cwd está. Suja: relata e deixa. Índice passa a `podada`.

No começo de cada atividade: `--prune` neste repo **antes** de abrir outra pasta, para o diretório não acumular entrega antiga.

## Red flags

- Worktree ou `-b` a partir de `develop`
- Editar em `main`/`master`/`develop`
- Segunda pasta para o mesmo slug
- Delivery que permanece no disco depois do PR
- Merge/rebase de develop na feature
- Um único PR “para os dois”
- Cherry-pick em cima de delivery antiga
- Merge ou deploy pelo agente
- Force push em `main`/`master` de repo compartilhado
- Declarar pronto sem linha no `ATIVIDADES.md` com URL de PR
- Deixar worktree `mergeada` no disco

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] `git fetch`; HEAD da atividade é ancestral-descendente de `origin/<produção>` no início
- [ ] Reuso conferido (`status.py --check-slug`); uma worktree por atividade
- [ ] Nome `{kind}/{YYYYMMDD}-{HHmm}-{slug}` e pasta `{YYYYMMDD}-{HHmm}-{kind}-{slug}` (com `{repo}` se a pasta for compartilhada), ou o do `AGENTS.md` do produto
- [ ] Zero merge de develop na atividade
- [ ] Delivery de produção por cherry-pick + PR; pasta delivery removida; develop idem se a branch existir
- [ ] `ATIVIDADES.md` reconciliado; URL de cada PR; checks green (não ausentes)
- [ ] Sem merge/deploy pelo agente; `status.py --prune` nas mergeadas (pasta some; suja não se força)
