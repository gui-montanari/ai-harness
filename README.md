# skills

Coleção pública de [Agent Skills](https://agentskills.io).

Cada skill é uma pasta com `SKILL.md`. O `name` no YAML **é o nome da pasta da skill** (última segmento), não o agrupador `backend/` / `frontend/`.

**Constituição:** [`AGENTS.md`](./AGENTS.md) — SSOT de princípios. Skills são o **como**. Não reescrevem o princípio.

## Árvore

```
architecture/              # desenho do sistema + gate de entrega
backend/
  auth/
  http-apis/
  mcp-servers/
  mcp-tools/
  oauth-connectors/        # ponte → auth
  sql-migrations/
  persistence-ports/
  sql-dialects/
  reliable-messaging/
  cache-ports/
  object-storage/
  observability/
  background-workers/
  agent-orchestration/
  orchestration-runtime/
  langgraph-agents/        # ponte → orchestration-runtime
  ops-backoffice/
frontend/
  frontend-surfaces/
  frontend-login/
  frontend-shell/
  frontend-chat/
  frontend-backoffice/
quality/
  cicd/
  skills-audit/
  principles-audit/
  security-audit/
shared/                    # scanner/PDF dos audits
```

## Skills

### Arquitetura e qualidade

| Skill | Quando |
|-------|--------|
| [`architecture`](./architecture/) | Desenhar limites, ADRs, onde mora cada capacidade. Gate: audits até zero. `/architecture` |
| [`cicd`](./quality/cicd/) | Workflows seguros, jobs, ruff/mypy/eslint, coverage, deploy por SHA. `/cicd` |
| [`skills-audit`](./quality/skills-audit/) | Coerência do catálogo; só achado com valor; veredito 10/10. `/skills-audit` |
| [`principles-audit`](./quality/principles-audit/) | Varredura hexagonal / TDD / `/api/v1`. `/principles-audit` |
| [`security-audit`](./quality/security-audit/) | Tenant, IDOR, XSS, segredos. `/security-audit` |

### Backend

| Skill | Quando |
|-------|--------|
| [`http-apis`](./backend/http-apis/) | REST `/api/v1`, schemas ≠ Command. `/http-apis` |
| [`auth`](./backend/auth/) | JWT, M2M, sessão, webhook HMAC, OAuth MCP. `/auth` |
| [`mcp-servers`](./backend/mcp-servers/) | Borda MCP: transporte, `/mcp`, perfis. `/mcp-servers` |
| [`mcp-tools`](./backend/mcp-tools/) | Tool atômica vs jornada; catálogo e perfil. `/mcp-tools` |
| [`sql-migrations`](./backend/sql-migrations/) | `YYYYMMDD_VV`; no mesmo dia acrescentar no arquivo. `/sql-migrations` |
| [`persistence-ports`](./backend/persistence-ports/) | DB só via porto; RLS. `/persistence-ports` |
| [`sql-dialects`](./backend/sql-dialects/) | Postgres/SQL Server pela DSN; tipos portáteis. `/sql-dialects` |
| [`reliable-messaging`](./backend/reliable-messaging/) | Outbox; RabbitMQ / Redis Streams / Service Bus. `/reliable-messaging` |
| [`cache-ports`](./backend/cache-ports/) | Cache derivado; Redis por porta; TTL. `/cache-ports` |
| [`object-storage`](./backend/object-storage/) | Upload, bucket privado, URL assinada. `/object-storage` |
| [`observability`](./backend/observability/) | Log, trace, métrica, sem PII. `/observability` |
| [`background-workers`](./backend/background-workers/) | API ≠ worker; drain; job single-flight. `/background-workers` |
| [`agent-orchestration`](./backend/agent-orchestration/) | Spec, um conversacional, guardas. `/agent-orchestration` |
| [`orchestration-runtime`](./backend/orchestration-runtime/) | Ativar o motor: in-process / Make / LangGraph. `/orchestration-runtime` |
| [`ops-backoffice`](./backend/ops-backoffice/) | Fila, atribuição, SLA, protocolo. `/ops-backoffice` |

### Frontend

| Skill | Quando |
|-------|--------|
| [`frontend-surfaces`](./frontend/frontend-surfaces/) | Tokens, tema, PT/EN, tabela, primitivos, home. `/frontend-surfaces` |
| [`frontend-login`](./frontend/frontend-login/) | Página e campos de acesso. `/frontend-login` |
| [`frontend-shell`](./frontend/frontend-shell/) | Sidebar esquerda, nav, dropdown do usuário. `/frontend-shell` |
| [`frontend-chat`](./frontend/frontend-chat/) | Lista de conversas + thread. `/frontend-chat` |
| [`frontend-backoffice`](./frontend/frontend-backoffice/) | Inbox de tickets, detalhe, timeline. `/frontend-backoffice` |

## Como usar

Instalação **na máquina do agente**, uma vez. Não copie este catálogo para dentro do produto.

```bash
git clone git@github.com:gui-montanari/skills.git ~/.local/share/gui-montanari-skills
~/.local/share/gui-montanari-skills/install.sh
```

O `install.sh` liga cada skill nas pastas de skills do usuário (Grok, Codex, Agy, Cursor e o Code CLI) e grava uma regra curta apontando para a [constituição](./AGENTS.md). Em outro notebook: o mesmo clone + `install.sh` (ou `git pull && ./install.sh` se o clone já existir).

O produto tem o **próprio** `AGENTS.md` (domínio, ADR, fase) e **não** vendor este repositório. Cada skill termina em **Conferência**. Depois: `/principles-audit` e `/security-audit` até **zero** achados (`architecture`). Para auditar **este** catálogo: `/skills-audit`.

## Convenção

`name` no frontmatter = nome da pasta da skill. Agrupadores `backend/` e `frontend/` não entram no `name`.

## Licença

MIT. Veja [LICENSE](./LICENSE).
