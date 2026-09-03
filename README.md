# ai-harness

Harness de desenvolvimento com IA: constituição, skills, rules e hooks.
Vale em qualquer produto. O produto **não** copia este repositório — só o `AGENTS.md` local.

| Camada | Pasta | O que é |
|--------|-------|---------|
| Constituição | [`AGENTS.md`](./AGENTS.md) | Princípio, processo, forma |
| Skills | `architecture/` `backend/` `frontend/` `quality/` | HOW de um recorte ([Agent Skills](https://agentskills.io)) |
| Rules | [`rules/`](./rules/) | Gate **sempre ligado** em todo projeto e todo host |
| Hooks | [`hooks/`](./hooks/) | Enforcement no host (o modelo não escolhe obedecer) |
| MCP | [`mcp/`](./mcp/) | Catálogo da máquina, wrappers, OAuth persistente |

Cada skill é uma pasta com `SKILL.md`. O `name` no YAML **é o nome da pasta da skill**, não o agrupador `backend/` / `frontend/`.

## Árvore

```
rules/                     # gates de processo (sempre ligados)
hooks/                     # catálogo + sync (Grok/Cursor/Claude/Agy/Gemini/Windsurf)
mcp/                       # catálogo MCP da máquina + wrappers (`grok-cli`, …)
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
  git-activity/
  debug-hypotheses/
  client-harness/
  skills-audit/
  principles-audit/
  security-audit/
shared/                    # scanner/PDF dos audits
```

## MCP da máquina

Vive neste repo, em [`mcp/`](./mcp/). Clone + `./install.sh` em qualquer notebook:

1. skills, rules, hooks;
2. wrappers em `~/bin` (`grok-cli`, `claude-cli`, …);
3. catálogo universal sincronizado nos hosts;
4. `mcp/secrets.example/*.env.example` copiados para `~/.config/ai-harness/secrets/` se ainda não existirem — preencha as chaves lá.

OAuth (Cloudflare, Make, Stripe) grava refresh token em `~/.mcp-auth` na primeira autorização; as sessões seguintes reusam. Servidor que é só desta máquina (VPS, cliente) entra em `~/.config/ai-harness/overlay/mcp/` — o git público não leva IP nem subscription.

Skills `mcp-servers` e `mcp-tools` continuam sendo o HOW da **borda MCP de um produto**. O catálogo em `mcp/` é o que o **host do agente** carrega.

## Skills

### Arquitetura e qualidade

| Skill | Quando |
|-------|--------|
| [`architecture`](./architecture/) | Desenhar limites, ADRs, onde mora cada capacidade. Gate: audits até zero. `/architecture` |
| [`cicd`](./quality/cicd/) | Workflows seguros, jobs, ruff/mypy/eslint, coverage, deploy por SHA. `/cicd` |
| [`git-activity`](./quality/git-activity/) | Worktree a partir da produção, dual delivery, PR green. `/git-activity` |
| [`debug-hypotheses`](./quality/debug-hypotheses/) | Defeito: hipóteses, refutar, causa, só então o patch. `/debug-hypotheses` |
| [`client-harness`](./quality/client-harness/) | Repo privado `{cliente}-harness`; overlay; skills no workspace. `/client-harness` |
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
git clone git@github.com:gui-montanari/ai-harness.git ~/projetos/ferramentas/ai-harness
~/projetos/ferramentas/ai-harness/install.sh
```

O clone de trabalho é esse diretório. `install.sh` aponta `~/.local/share/ai-harness` para ele (hosts e wrappers leem o caminho canônico). Não trabalhe em `~/.local/share`.

O `install.sh` liga skills, [rules](./rules/), [hooks](./hooks/) e [mcp](./mcp/) em
**todos** os hosts conhecidos (Grok, Cursor, Claude Code, Codex, Agents,
Gemini/Antigravity, Windsurf, OpenCode). Cada host recebe **um** canal nativo;
o Grok não varre rules/hooks/skills/MCP/`CLAUDE.md` de Cursor ou Claude.
Overlay de cliente fica em `~/.config/ai-harness/overlay/{rules,hooks,mcp}/` e
não entra neste repo. O SSOT é o `{cliente}-harness` privado (skill `client-harness`);
o `install.sh` dele projeta o overlay.
Em outro notebook: o mesmo clone + `install.sh` (ou `git pull && ./install.sh`),
depois o `{cliente}-harness` de cada cliente em que for trabalhar.

O produto tem o **próprio** `AGENTS.md` (domínio, ADR, fase). Cada skill termina em **Conferência**.
Depois: `/principles-audit` e `/security-audit` até **zero** achados (`architecture`).
Para auditar **este** catálogo: `/skills-audit`.

## Convenção

`name` no frontmatter = nome da pasta da skill. Agrupadores `backend/` e `frontend/` não entram no `name`.

## Licença

MIT. Veja [LICENSE](./LICENSE).
