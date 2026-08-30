---
name: cicd
description: >
  Use when creating or changing GitHub Actions, GitLab CI, Makefile CI
  targets, coverage floor, ruff, mypy, eslint, tsc, import-linter,
  required checks, deploy workflow, OIDC, or when the user mentions
  CI, CD, pipeline, workflow.yml, gates, or /cicd. Secure workflows
  and jobs that fail closed and respect hexagonal architecture.
---

# CI/CD seguro

O pipeline **é** o gate de arquitetura em toda mudança. Se o CI não barra o vazamento, o vazamento existe. Makefile é o SSOT de *como rodar*; o workflow só chama os alvos. CD promove artefato **já construído** — não reconstrói “parecido”.

**REQUIRED BACKGROUND:** constituição `AGENTS.md` §4 (stack, `make lint`/`typecheck`/`test`) e §7 (Docker + CI). Imagem/compose: §7, não esta skill. Schema no CI: `sql-migrations`. Audits humanos: `principles-audit` e `security-audit`. O agente **não** mergeia nem faz deploy porque o CI ficou verde.

## Antes de implementar — pergunte

Se o host de CI **ainda não** está no ADR/`AGENTS.md`:

> Onde roda o CI neste produto?
> 1. GitHub Actions (canônico)
> 2. GitLab CI
> 3. Outro (nomeie)

Implemente **um**. Dois YAML “por se acaso” é YAGNI. Os jobs e o Makefile são os mesmos; só o host muda.

## Makefile — o CI chama isto

Na raiz, os alvos existem e **falham** (exit ≠ 0). Ninguém documenta um comando que o Makefile não tem.

```
make lint            # ruff check + ruff format --check  |  eslint
make typecheck       # mypy  |  tsc --noEmit
make test            # unit + contract + coverage floor
make check-architecture   # import-linter  |  dependency-cruiser
make check-migrations
make build           # imagem multi-stage, non-root, tag = git SHA
```

Python no `lint`: `ruff check .` **e** `ruff format --check .`. CI **não** roda `ruff check --fix` (mutação). TypeScript: `eslint` + `tsc --noEmit`. Fronteiras: se o linter de import não roda no CI, a regra hexagonal é teatro.

Coverage é **piso**, não troféu. Um número no `pyproject.toml` / `vitest` (`--cov-fail-under` / `thresholds`). Queda abaixo do piso falha o job. Não chase % de linha; cubra comportamento de `core/` e `application/`.

`make test` no PR = unit + contract. Integration/e2e só no job que **sobe** a infra (serviço Postgres/fila). Job sem infra **não** existe com `|| true`.

## Workflows — dois arquivos, dois motivos

| Arquivo | Faz | Não faz |
|---------|-----|---------|
| `ci.yml` | verificar o SHA (lint, types, testes, fronteiras, migrations, build) | deploy, push de imagem para prod, secrets de cloud |
| `deploy.yml` | promover o artefato **desse** SHA | rebuild, rodar em fork, pular os gates |

Jobs **separados** (um gate = um job). Falha de ruff não se esconde atrás de um `script:` de 40 linhas. Paralelo depois do checkout; `fail-fast: false` no conjunto para ver todos os vermelhos.

### CI (forma)

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
defaults:
  run:
    shell: bash

jobs:
  lint:
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>   # pin SHA; tag @v4 se move
        with:
          persist-credentials: false
      - run: make lint
  typecheck:
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>
        with:
          persist-credentials: false
      - run: make typecheck
  test:
    timeout-minutes: 20
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>
        with:
          persist-credentials: false
      - run: make test
  architecture:
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>
        with:
          persist-credentials: false
      - run: make check-architecture
  migrations:
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>
        with:
          persist-credentials: false
      - run: make check-migrations
  image:
    timeout-minutes: 20
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<sha>
        with:
          persist-credentials: false
      - run: make build
```

Actions **pinadas por SHA** (40 hex), não `@v4`. `persist-credentials: false`. Todo job tem `timeout-minutes`. `permissions:` no workflow **e** no job — default do host é largo demais; aqui o default é `contents: read`.

### CD (forma)

Workflow **à parte**. Disparo: `workflow_dispatch` e/ou push na branch protegida **depois** do CI verde. Job de deploy:

- `environment: production` (ou `staging`) com reviewer obrigatório no host
- `permissions: { contents: read, id-token: write }` — OIDC para a cloud; **sem** access key de longa vida no repo
- puxa a imagem/artefato tagueado com o **mesmo** git SHA que o `make build` do CI
- não faz checkout de PR de fork; não tem secret se `github.event.pull_request.head.repo.fork == true`
- não usa `pull_request_target` com checkout do head do PR (é execução de código não confiável com o token da base)

Agente **não** aperta o deploy. CI verde ≠ licença.

Dois ambientes (dev/prod) **não** se misturam por merge de branch longa. Entrega seletiva quando o `AGENTS.md` local mandar.

## Segurança do workflow (indústria)

- Least privilege. `permissions: write-all` / omitir `permissions` = achado.
- Sem `|| true`, sem `continue-on-error: true`, sem `set +e` em lint, typecheck, test, architecture, migrations, scan. Gate que não reprova **não é gate**.
- Sem segredo em `echo`, em `run: |` interpolado, em argumento de CLI, em log de exception. `set +x` não disfarça `${{ secrets.* }}` expandido.
- PR de fork: nenhum secret, nenhum OIDC, nenhum push de imagem. `pull_request` (não `_target`) para CI.
- Scanner de segredo no CI (`gitleaks` / equivalente do host) **e** secret scanning nativo do host. Falha o job.
- Imagem: scan de CVE no job `image` (Trivy ou equivalente); HIGH/CRITICAL falha. Constituição §7: non-root, multi-stage, sem `.git`/`.env`, tag SHA, nunca `latest` como versão.
- Dependências: lockfile commitado; `setup-python`/`setup-node` com cache **no lockfile**; sem `pip install` / `npm i` solto na imagem de prod.
- `CODEOWNERS` cobre `.github/workflows/` e o `Makefile`. Mudança de pipeline não passa sem reviewer.
- Dependabot (ou equivalente) no ecossistema `github-actions` / imagens.
- Branch protegida: required status = **todos** os jobs acima; sem bypass de admin no dia a dia; sem force-push.

GitLab: mesmos alvos; `rules:` no lugar de `on:`; `id_tokens` para OIDC; `CI_JOB_TOKEN` least-privilege por job. Não copie YAML de GitHub “traduzido”.

## O que o CI prova da arquitetura

| Job | Invariante |
|-----|------------|
| `lint` / `typecheck` | o código é o que o repo diz que é |
| `test` (unit+contract) | regra e porto; coverage floor |
| `architecture` | `core`/`application` sem SDK; fronteira hexagonal |
| `migrations` | filename `YYYYMMDD_VV`; um runner |
| `image` | o SHA é implantável; scan não é opcional se há container |

Testes em `tests/architecture/` **entram** no job `architecture` (ou em `test` se o Makefile unificar — um dono). Diretório de produção fora do linter de import = gate mal configurado.

## Red flags — PARE

- Workflow sem `permissions:` ou com `write-all`
- Action por tag móvel (`@v4`) sem pin de SHA
- `|| true` / `continue-on-error` em gate
- `ruff check --fix` / format que altera o tree no CI
- Um job só chamado `build` que esconde lint+test
- Coverage como badge, sem `--cov-fail-under`
- CI que não chama o Makefile (comandos copiados no YAML = segundo dono)
- `pull_request_target` + checkout do fork
- Secret de cloud de longa vida; deploy sem `environment` / sem OIDC
- Rebuild no deploy em vez de promover o SHA
- `latest` como tag de produção
- Agente mergeando ou deployando porque “o CI passou”
- Dois hosts de CI no mesmo repo sem segundo ambiente real

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Host perguntado (ou já no ADR); **um** pipeline
- [ ] Makefile é SSOT; CI chama `lint` `typecheck` `test` `check-architecture` `check-migrations` `build`
- [ ] `ruff check` + `ruff format --check` (ou eslint + `tsc --noEmit`); sem `--fix` no CI
- [ ] Coverage com piso que falha o job
- [ ] Jobs separados; `permissions: contents: read`; actions pinadas por SHA; timeout; sem `|| true`
- [ ] `ci.yml` ≠ `deploy.yml`; CD promove o SHA; OIDC + `environment`; nada em fork
- [ ] Scanner de segredo + scan da imagem; `CODEOWNERS` em workflows
- [ ] Agente não mergeou nem fez deploy
