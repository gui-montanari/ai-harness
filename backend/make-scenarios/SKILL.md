---
name: make-scenarios
description: >
  Use when the user mentions Make.com scenario, blueprint, IML, Make module,
  Make webhook, scenarios_create, make-scenario-building, make-module-configuring,
  or Make Agent Skills. Canonical for the product runtime adapter is
  orchestration-runtime. Authoring a scenario in the Make account uses the
  official Make skills plus MCP — not a second HOW in this harness.
---

# Make.com: duas casas

**REQUIRED SUB-SKILL:** `orchestration-runtime` (+ spec em `agent-orchestration`) se o recorte for o **adapter do produto**. Se o recorte for montar, validar ou deployar **cenário na conta Make**: leia as Agent Skills oficiais e use o MCP `https://mcp.make.com`. Não copie a doc do Make para este repositório.

Dois trabalhos — classifique **antes** de editar:

| Recorte | Dono | Não é |
|---------|------|--------|
| Runtime do produto (`GraphSpec` → adapter Make) | `orchestration-runtime` | Cenário na conta Make |
| Blueprint, módulo, conexão, webhook, IML na conta Make | Skills oficiais + MCP da máquina | Segundo HOW em `backend/` |

Skills oficiais (MIT, [integromat/make-skills](https://github.com/integromat/make-skills), [skills.make.com](https://skills.make.com/)): `make-scenario-building`, `make-module-configuring`, `make-mcp-reference`, `make-api-shell-connection-workflow`. O `install.sh` clona o cache em `~/.local/share/make-skills` e liga o que `skills.publish.json` listar em `~/.cursor/skills` e `~/.agents/skills`. Não vendoriza neste git.

Make.com ou LangGraph é **um** adapter da mesma porta — skill `orchestration-runtime` pergunta qual, e implementa **um**. Não desenhe o domínio em cenário Make. Não instale LangGraph “para depois trocar por Make”.

Ação ao vivo: as skills oficiais e o MCP alteram cenário e conexão na conta. Conta de teste antes de produção.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Classifiquei o recorte: adapter de produto vs cenário na conta Make
- [ ] Adapter: li e marquei a conferência de `orchestration-runtime` (e `agent-orchestration` se o spec mudou)
- [ ] Conta Make: li as skills oficiais presentes em `~/.cursor/skills`; não reescrevi o HOW delas neste git
- [ ] Sem pasta `backend/make-*` com a doc do Make; sem segundo runtime “para ter Make e LangGraph”
