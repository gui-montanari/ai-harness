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
  oauth-connectors/        # ponte → auth
  sql-migrations/
  persistence-ports/
  agent-orchestration/
  langgraph-agents/        # ponte → agent-orchestration
frontend/
  frontend-surfaces/
  frontend-login/
  frontend-shell/
  frontend-chat/
quality/
  principles-audit/
  security-audit/
shared/                    # scanner/PDF dos audits
```

## Skills

### Arquitetura e qualidade

| Skill | Quando |
|-------|--------|
| [`architecture`](./architecture/) | Desenhar limites, ADRs, onde mora cada capacidade. Gate: audits até zero. `/architecture` |
| [`principles-audit`](./quality/principles-audit/) | Varredura hexagonal / TDD / `/api/v1`. `/principles-audit` |
| [`security-audit`](./quality/security-audit/) | Tenant, IDOR, XSS, segredos. `/security-audit` |

### Backend

| Skill | Quando |
|-------|--------|
| [`http-apis`](./backend/http-apis/) | REST `/api/v1`, schemas ≠ Command. `/http-apis` |
| [`auth`](./backend/auth/) | JWT, M2M, sessão, webhook HMAC, OAuth MCP. `/auth` |
| [`mcp-servers`](./backend/mcp-servers/) | Borda MCP: tools = use cases. `/mcp-servers` |
| [`sql-migrations`](./backend/sql-migrations/) | `YYYYMMDD_VV`; no mesmo dia acrescentar no arquivo. `/sql-migrations` |
| [`persistence-ports`](./backend/persistence-ports/) | DB só via porto; RLS. `/persistence-ports` |
| [`agent-orchestration`](./backend/agent-orchestration/) | Spec neutro; Make/LangGraph são adapters. `/agent-orchestration` |

### Frontend

| Skill | Quando |
|-------|--------|
| [`frontend-surfaces`](./frontend/frontend-surfaces/) | Tokens, área pública (hero reativo), i18n, `ui/`. `/frontend-surfaces` |
| [`frontend-login`](./frontend/frontend-login/) | Página e campos de acesso. `/frontend-login` |
| [`frontend-shell`](./frontend/frontend-shell/) | Sidebar esquerda, nav, dropdown do usuário. `/frontend-shell` |
| [`frontend-chat`](./frontend/frontend-chat/) | Thread: bolha, composer, thinking. `/frontend-chat` |

## Como usar

```bash
git clone https://github.com/gui-montanari/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.grok/skills
find architecture backend frontend quality -name SKILL.md | while read -r f; do
  d=$(dirname "$f")
  name=$(basename "$d")
  ln -sfn "$(pwd)/$d" ~/.agents/skills/"$name"
  ln -sfn "$(pwd)/$d" ~/.grok/skills/"$name"
done
```

Copie `AGENTS.md` para a raiz de cada produto. Depois de implementar: `/principles-audit` e `/security-audit` até **zero** achados (`architecture`).

## Convenção

`name` no frontmatter = nome da pasta da skill. Agrupadores `backend/` e `frontend/` não entram no `name`.

## Licença

MIT. Veja [LICENSE](./LICENSE).
