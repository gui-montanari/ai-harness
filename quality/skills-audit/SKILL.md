---
name: skills-audit
description: >
  Use when auditing this skills catalog for consistency, gaps, contradictions,
  or whether it is 10/10. Also when the user asks another model to review all
  skills, check for inconsistencies, missing coverage of architecture or
  development standards, or runs /skills-audit. Not for product code — that is
  principles-audit and security-audit. Report only findings with real value;
  ignore cosmetics.
---

# Auditoria do catálogo de skills

Esta skill audita **o repositório de skills** (constituição + cada `SKILL.md`), não o código de um produto. Produto: `principles-audit` / `security-audit`.

O objetivo é saber se um agente que só lê este catálogo implementa certo — e se o catálogo ainda ensina os padrões de arquitetura e desenvolvimento da constituição. Cosmético não entra no relatório.

**10/10** = zero achados `bloqueante` e zero `material`. Backlog de melhoria **não** tira o 10. Não invente nota 7/10 por prosa.

**REQUIRED BACKGROUND:** `AGENTS.md` desta coleção (SSOT de princípios). Skills são o **como**. Não reescrevem o princípio.

## Checklist (copie e marque)

```
- [ ] 0. Confirmar o alvo: pasta das skills (não o produto)
- [ ] 1. Ler AGENTS.md inteiro
- [ ] 2. Inventário de todo SKILL.md (não amostrar)
- [ ] 3. Catálogo cruzado: árvore README (inclui `rules/` e `hooks/`), tabelas README, architecture «Onde mora», name=pasta
- [ ] 4. Cada skill lida por completo; Conferência presente e cobre as invariantes dela
- [ ] 5. Pontes redirecionam; colisões XOR apontam para o dono certo
- [ ] 6. Constituição × skill: sem contradição, sem segundo dono da mesma regra
- [ ] 7. HOW gap: princípio sem procedimento só vira achado se o agente inventaria errado
- [ ] 8. Cosmético descartado (contar, não listar)
- [ ] 9. Relatório: achados com valor + cobertura do que está coerente + backlog opcional
- [ ] 10. Veredito 10/10 só com zero bloqueante/material. Sem corrigir a menos que o humano peça
```

Não feche sem o inventário completo e sem o veredito explícito.

## O que não é achado

Descarte em silêncio (só o **número** no relatório):

- “poderia ser mais claro”, tom, emoji, diagrama, ordem de seções
- skill mais curta que a vizinha
- mais exemplos “por se acaso”
- sinonímia correta (CI = pipeline, porto = porta)
- hífen, maiúscula de título, reformular frase já certa
- traduzir identificador de mercado
- segunda skill de provider sem segundo ambiente real (isso é YAGNI cumprido, não buraco)
- ponte ausente da tabela «Quando» do README — regra: ponte entra na **árvore**, não na tabela de execução

Se o único efeito da mudança é estética, **não é valor**.

## O que é valor

| Severidade | Só se isto for verdade |
|------------|------------------------|
| `bloqueante` | Agente seguiria a skill e violaria a constituição, criaria segundo dono, ou iria para a skill errada |
| `material` | Catálogo mente (skill órfã, tabela desatualizada, conferência teatro, ponte que não redireciona, constituição × skill divergentes no HOW) |
| `melhoria` | Melhora real e durável, **sem** a qual o agente ainda acerta. Não bloqueia 10/10 |

Todo achado: `arquivo:linha` (ou skill + seção), o que o agente faria de errado, **dono do fato** (um), correção mínima. Sem reescrever o catálogo no relatório.

## Passo 0 — Alvo

Raiz = repositório `skills` **ou** a pasta `skills/` vendorizada num produto. Ignore `backend/`, `frontend/` e apps do produto. Se o humano pediu auditoria de código, pare e use as skills de audit de produto.

## Passo 2 — Inventário

```bash
find architecture backend frontend quality -name SKILL.md | sort
ls rules/*.md | grep -v README
ls hooks/catalog.json hooks/sync.py hooks/scripts
```

`rules/` e `hooks/` **não** são skill (não têm `SKILL.md`). Têm de aparecer na árvore do README. Overlay local do host (`stockfy-repos-autorizacao` e similares) **não** mora neste repo. `mcp-cli-toolkit` é repo irmão **privado** — ausência aqui não é achado.

Para cada um registre:

```
pasta  name(yaml)  ponte?  conferência?  no README árvore?  no README tabela?  no architecture «Onde mora»?
```

`name` no YAML **é** o basename da pasta. Agrupador `backend/` / `frontend/` / `quality/` não entra no `name`.

**Ponte** (hoje): `oauth-connectors` → `auth`; `langgraph-agents` → `orchestration-runtime` (+ spec em `agent-orchestration`); `channel-evolution` → `whatsapp-channel`. Ponte: SKILL.md curto, redireciona na primeira tela, `REQUIRED SUB-SKILL` da canônica. Não compete na tabela «Quando».

`shared/` não é skill.

## Passo 3 — Superfícies do catálogo

Têm de contar a **mesma** coleção, com papéis distintos:

| Superfície | Contém |
|------------|--------|
| Árvore do README | toda pasta com `SKILL.md`, inclusive pontes; e `rules/`, `hooks/` |
| Tabelas «Quando» do README | skills de execução (não pontes) |
| `architecture` «Onde mora» | capacidades de **produto** → skill canônica. Não lista pontes nem audits de catálogo (`skills-audit`, `principles-audit`, `security-audit`) |
| Constituição §3 (lista de skills) | HOW de produto. Não é inventário desta auditoria |

Skill no disco fora da árvore ou da tabela de execução = `material`. Tabela apontando para pasta inexistente = `material`. `name` ≠ pasta = `bloqueante` (o host carrega pelo `name`).

## Passo 5 — Colisões (as duas pontas)

Cada par tem de dizer, dos dois lados, o que **não** é desta skill. Ausência de XOR = agente no recorte errado = `bloqueante` se a description também colide; senão `material`.

| Recorte A | Recorte B | Fronteira |
|-----------|-----------|-----------|
| `frontend-chat` | `frontend-backoffice` | conversa de produto ≠ fila de ticket |
| `frontend-shell` | `frontend-chat` | UserMenu: um sul só |
| `cache-ports` | `reliable-messaging` | Redis cache ≠ stream/fila |
| `persistence-ports` | `sql-dialects` / `sql-migrations` | porto/RLS ≠ dialeto ≠ filename |
| `object-storage` | `persistence-ports` | blob ≠ linha SQL |
| `ops-backoffice` | `frontend-backoffice` | domínio da fila ≠ UI |
| `http-apis` | `mcp-servers` | REST ≠ transporte MCP |
| `mcp-servers` | `mcp-tools` | processo/transporte ≠ o que entra em `tools/list` |
| `mcp-tools` | `agent-orchestration` | publicação MCP ≠ `tools/` interno do grafo |
| `auth` | `oauth-connectors` | um catálogo; ponte só dispara OAuth de host |
| `agent-orchestration` | `orchestration-runtime` | ConversationalEngine + specs/<job> ≠ adapter de processo |
| `orchestration-runtime` | `background-workers` | execute_turn ≠ supervisor de processo |
| `orchestration-runtime` | `langgraph-agents` | porta/capabilities ≠ StateGraph no adapter |
| `whatsapp-channel` | `agent-orchestration` | envelope de canal ≠ turno do agente |
| `channel-evolution` | `whatsapp-channel` | ponte Evolution ≠ skill canônica do canal |
| `cicd` | `sql-migrations` | job de CI ≠ regra de filename |
| `observability` | `http-apis` | log/trace ≠ `/health`/`/ready` |
| `cicd` | `principles-audit` / `security-audit` | pipeline ≠ varredura humana do diff |

Description YAML que dispara a skill errada (ex.: “ticket” em `frontend-chat`) é `bloqueante`.

## Passo 6 — Constituição × HOW

Princípio vive em `AGENTS.md`. Skill aponta e ensina o procedimento.

Achado:

- Skill **enfraquece** a constituição (`|| true` no CI, SDK no `core`, segundo provider “por se acaso”, merge pelo agente)
- Skill **copia** tabela/lista que tem dono na constituição (amanhã divergem). Apontar não é copiar; reescrever a tabela de camadas é
- Constituição e skill mandam HOW **diferente** (alvos do Makefile, nome de migration, lugar do Pydantic)
- Skill sem `REQUIRED BACKGROUND` quando o procedimento depende de uma seção da constituição **e** o agente, sem ela, inventa a regra

Não é achado: skill curta que aponta para a seção certa.

## Passo 7 — Buraco de HOW e padrão novo

Propor skill nova **somente** se as três forem verdade:

1. A constituição (ou um padrão que os agentes já repetem) exige um procedimento.
2. Nenhuma skill existente é o dono, nem por ponte.
3. Sem a skill, o agente **inventa** o HOW (não: “ficaria bonito ter”).

Isso é `melhoria` se o agente ainda consegue acertar lendo a constituição; `material` se a evidência é que ele inventa errado. Não crie a pasta no relatório. Uma linha: dono sugerido + por quê.

YAGNI: feature flags, segundo APM, OCR, nanoserviço, portal futuro — ausência **não** é buraco.

## Conferência da skill auditada

Toda skill termina em **Conferência**. Caixas = invariantes **dela**, testáveis no diff. Teatro (caixas genéricas que qualquer skill marcaria) = `material`. Ponte: conferência = “li a canônica” + o único fato da ponte.

## Relatório (chat)

Nesta ordem. Sem PDF, sem arquivo novo, sem PR.

1. Alvo (path) e N de `SKILL.md`.
2. Matriz do inventário (passo 2). Furow: qualquer `não`.
3. Achados `bloqueante` / `material` — `arquivo:linha`, valor, dono, correção mínima.
4. Cobertura: o que foi verificado e está coerente (prova que não amostraram).
5. Cosméticos descartados: **só a conta**.
6. Backlog `melhoria` em checkboxes — vazio é o estado saudável:

```
## Backlog (não bloqueia 10/10)
- [ ] …
```

7. Veredito: **10/10** ou **não 10/10** + a lista curta do que falta para o 10.

Não corrija o catálogo a menos que o humano peça. Se pedir: um dono por fato, sem passe cosmético no mesmo diff.

## Red flags — PARE

- Amostragem (“olhei as principais”)
- Achado sem valor (“eu reescreveria assim”)
- Nota 8/10 por estilo
- Inventar skill nova no relatório sem as três condições do passo 7
- Auditar código de produto com esta skill
- Corrigir sem o humano ter pedido
- Listar cosmético “para ficar completo”

## Conferência

A checklist do topo **é** a conferência desta skill. Todas as caixas marcadas + veredito explícito antes de entregar.
