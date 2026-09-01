# ai-harness

Harness de desenvolvimento com IA: constituição, skills, rules e hooks.
Vale em qualquer produto. O produto **não** copia este repositório — só o `AGENTS.md` local.

| Camada | Pasta | O que é |
|--------|-------|---------|
| Constituição | [`AGENTS.md`](./AGENTS.md) | Princípio, processo, forma |
| Skills | `architecture/` `backend/` `frontend/` `quality/` | HOW de um recorte ([Agent Skills](https://agentskills.io)) |
| Rules | [`rules/`](./rules/) | Gate **sempre ligado** em todo projeto e todo host |
| Hooks | [`hooks/`](./hooks/) | Enforcement no host (o modelo não escolhe obedecer) |
| MCP | repo **privado** `mcp-cli-toolkit` | Catálogo, wrappers, servidores — não entra aqui |

Cada skill é uma pasta com `SKILL.md`. O `name` no YAML **é o nome da pasta da skill**, não o agrupador `backend/` / `frontend/`.

## Árvore

```
rules/                     # gates de processo (sempre ligados)
hooks/                     # catálogo + sync (Grok/Cursor/Claude/Agy/Gemini/Windsurf)
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
  whatsapp-channel/
  channel-evolution/       # ponte → whatsapp-channel
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

## MCP (repo irmão, privado)

`gui-montanari/mcp-cli-toolkit` é **privado**: perfis de cliente, VPS, secrets de máquina.
Não se mistura neste repo público. O `install.sh` deste harness chama o do toolkit
se o clone existir em `~/projetos/ferramentas/mcp-cli-toolkit` ou
`~/.local/share/mcp-cli-toolkit`.

Skills `mcp-servers` e `mcp-tools` ensinam a **borda MCP de um produto**.
O toolkit ensina a **máquina do agente** (quais MCPs o host carrega).

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
| [`agent-orchestration`](./backend/agent-orchestration/) | Motor conversacional + specs/<job>, guardas. `/agent-orchestration` |
| [`orchestration-runtime`](./backend/orchestration-runtime/) | Ativar o runtime de processo: in-process / Make / LangGraph. `/orchestration-runtime` |
| [`ops-backoffice`](./backend/ops-backoffice/) | Fila, atribuição, SLA, protocolo. `/ops-backoffice` |
| [`whatsapp-channel`](./backend/whatsapp-channel/) | WhatsApp: porta de canal; Evolution e Twilio são adapters. `/whatsapp-channel` |

### Frontend

| Skill | Quando |
|-------|--------|
| [`frontend-surfaces`](./frontend/frontend-surfaces/) | Tokens, tema, PT/EN, tabela, primitivos, home. `/frontend-surfaces` |
| [`frontend-login`](./frontend/frontend-login/) | Página e campos de acesso. `/frontend-login` |
| [`frontend-shell`](./frontend/frontend-shell/) | Sidebar esquerda, nav, dropdown do usuário. `/frontend-shell` |
| [`frontend-chat`](./frontend/frontend-chat/) | Lista de conversas + thread. `/frontend-chat` |
| [`frontend-backoffice`](./frontend/frontend-backoffice/) | Inbox de tickets, detalhe, timeline. `/frontend-backoffice` |

## Como usar

Instalação **na máquina do agente**, uma vez.

```bash
git clone git@github.com:gui-montanari/ai-harness.git ~/.local/share/ai-harness
~/.local/share/ai-harness/install.sh
```

O `install.sh` liga skills, [rules](./rules/) e [hooks](./hooks/) em **todos** os hosts
conhecidos (Grok, Cursor, Claude Code, Codex, Agents, Gemini/Antigravity, Windsurf,
OpenCode): skills/rules por symlink; hooks por catálogo + adapter, no mesmo espírito do
`mcp-cli-toolkit`. Overlay de cliente fica em `~/.config/ai-harness/overlay/` e não entra
neste repo. Se o toolkit MCP privado estiver na máquina, o install chama-o também.
Em outro notebook: o mesmo clone + `install.sh` (ou `git pull && ./install.sh`).

O produto tem o **próprio** `AGENTS.md` (domínio, ADR, fase). Cada skill termina em **Conferência**.
Depois: `/principles-audit` e `/security-audit` até **zero** achados (`architecture`).
Para auditar **este** catálogo: `/skills-audit`.

## Convenção

`name` no frontmatter = nome da pasta da skill. Agrupadores `backend/` e `frontend/` não entram no `name`.

## Licença

MIT. Veja [LICENSE](./LICENSE).
