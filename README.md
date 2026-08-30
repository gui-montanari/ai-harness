# skills

Coleção pública de [Agent Skills](https://agentskills.io).

Cada skill é uma pasta com um `SKILL.md` (metadados + instruções) e, quando necessário, scripts e referências.

**Constituição:** [`AGENTS.md`](./AGENTS.md) — SSOT de princípios. Copie para a raiz do produto. Skills são o **como** (árvore, receita, red flags) e não reescrevem o princípio.

## Skills

| Skill | Quando usar |
|-------|-------------|
| [`security-audit`](./security-audit/) | Auditoria: tenant, authz só no frontend, IDOR, segredos, XSS. `/security-audit` |
| [`principles-audit`](./principles-audit/) | Varredura contra o `AGENTS.md` (hexagonal, TDD, `/api/v1`, migrations). `/principles-audit` |
| [`http-apis`](./http-apis/) | REST `/api/v1`, schemas ≠ Command, OpenAPI. `/http-apis` |
| [`mcp-servers`](./mcp-servers/) | Borda MCP para Grok/Cursor: tools = use cases, Streamable HTTP. `/mcp-servers` |
| [`oauth-connectors`](./oauth-connectors/) | OAuth Authorization Code + PKCE para conector de LLM (Grok). `/oauth-connectors` |
| [`sql-migrations`](./sql-migrations/) | `YYYYMMDD_VV`; no mesmo dia **acrescentar** no arquivo, não multiplicar. `/sql-migrations` |
| [`agent-orchestration`](./agent-orchestration/) | Agente de produto: spec neutro, Make/LangGraph só adapter, um agente no v1. `/agent-orchestration` |
| [`langgraph-agents`](./langgraph-agents/) | Ponte: LangGraph é adapter. Use `agent-orchestration`. |
| [`persistence-ports`](./persistence-ports/) | DB/Redis/blob só via porto; RLS; grafo e rota sem driver. `/persistence-ports` |
| [`frontend-surfaces`](./frontend-surfaces/) | React, `ui/`, i18n PT/EN, tokens por tenant, home tipo Autodin. `/frontend-surfaces` |
| [`frontend-chat`](./frontend-chat/) | Thread ChatGPT: bolha, composer, thinking; casca do stockfy-ai sem SSE/HITL. `/frontend-chat` |

## Como usar

Clone o repositório e aponte **todas** as skills para o runtime do agente (symlink):

```bash
git clone https://github.com/gui-montanari/skills.git
cd skills
mkdir -p ~/.agents/skills ~/.grok/skills
for s in security-audit principles-audit http-apis mcp-servers oauth-connectors \
         sql-migrations agent-orchestration langgraph-agents persistence-ports \
         frontend-surfaces frontend-chat; do
  ln -sfn "$(pwd)/$s" ~/.agents/skills/$s
  ln -sfn "$(pwd)/$s" ~/.grok/skills/$s
done
```

Copie `AGENTS.md` para a raiz de cada produto novo (ou estenda o local, sem enfraquecer). No chat: `/http-apis`, `/langgraph-agents`, `/sql-migrations`, …

## Convenção

```
AGENTS.md                 # constituição (copie para o produto)
shared/                   # gerador de PDF + scanner (SSOT)
<nome-da-skill>/
  SKILL.md
  references/
```

`name` no frontmatter YAML deve coincidir com o nome da pasta.

## Licença

MIT. Veja [LICENSE](./LICENSE).
