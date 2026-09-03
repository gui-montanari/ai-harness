---
description: Analisar o pedido, ler a constituição e confirmar skill antes de implementar.
alwaysApply: true
---

# Analisar e checar skill antes de implementar

Vale em todo projeto. O `AGENTS.md` do produto prevalece no local (domínio, ADR, fase).
A constituição do harness prevalece em princípio, processo e forma.

Proibido editar código, criar arquivo ou aplicar patch sem os dois gates.

## Gate 1 — Analisar

Antes da primeira edição, no chat (2–4 linhas):

1. O pedido de fato (não o conveniente).
2. Arquivos, módulos e contratos tocados.
3. O que o repo já tem para reutilizar.
4. O que não se inventa (HOW, padrão, fluxo).

Sem invariante clara: plano ou pergunta — não código.
Defeito, falha, regressão ou teste vermelho: rule e skill `debug-hypotheses` **antes** de qualquer patch.
Contrato publicado, breaking change ou trava nova: rule `ask-before-contract` — explique e espere o “pode” deste turno.
Leia a constituição: `~/.local/share/ai-harness/AGENTS.md`.

## Gate 2 — Confirmar skill

Procure a skill do recorte. Não confie na memória. Leia o `SKILL.md` inteiro; não anuncie o nome e siga de memória.

Onde olhar: skills listadas na sessão; `~/.grok/skills/`, `~/.cursor/skills/`,
`~/.codex/skills/`; pasta de skills do Code CLI; e as pastas `skills/` do repo.

**Kit de trabalho** — esta tabela é o dono (processo **e** produto). Constituição e `architecture` **apontam**; não copiam. O pedido mente: se o recorte **contém** o sinal, a linha entra mesmo que o humano não a tenha citado. Pontes (`oauth-connectors`, `langgraph-agents`, `channel-evolution`) não competem aqui.

### Processo

| Trabalho | Ler |
|----------|-----|
| defeito, falha, regressão, teste vermelho | `debug-hypotheses` (log/Azure/WMS: skill de cliente, se houver) |
| worktree, branch, dual delivery, PR | `git-activity` |
| desenhar ou analisar o desenvolvimento | `architecture` — depois as linhas de produto que o recorte contém |
| harness de cliente, overlay | `client-harness` |
| auditar o catálogo de skills | `skills-audit` |
| auditar o diff do produto | `principles-audit` + `security-audit` (`architecture` manda no gate de entrega) |
| CI, workflow, Compose, coverage | `cicd` |
| contrato publicado, breaking, trava/guarda nova na borda | pare — rule `ask-before-contract`; não edite sem o “pode” |

### Produto — backend

| Trabalho | Ler |
|----------|-----|
| REST, OpenAPI, webhook HTTP | `http-apis` |
| sessão, JWT, OAuth, HMAC, papel | `auth` |
| MCP transporte `/mcp` | `mcp-servers` |
| MCP tool, jornada, perfil | `mcp-tools` |
| schema SQL, migration | `sql-migrations` |
| dois SGBD / DSN | `sql-dialects` |
| repositório, RLS, tenant no SQL | `persistence-ports` + `sql-migrations` |
| cache Redis | `cache-ports` |
| upload, blob, URL assinada | `object-storage` |
| log, trace, métrica | `observability` |
| outbox, evento, consumer | `reliable-messaging` + `background-workers` |
| worker, job, scheduler | `background-workers` |
| agente, turno, specs, guarda | `agent-orchestration` + `orchestration-runtime` |
| WhatsApp | `whatsapp-channel` (+ `http-apis` no webhook) |
| fila, atribuição, SLA, protocolo | `ops-backoffice` (+ UI: linha backoffice) |

### Produto — frontend

Toda UI herda `frontend-surfaces` (tokens, tema, PT/EN, viewport). Some a skill da **superfície** tocada:

| Trabalho | Ler |
|----------|-----|
| tokens, tema, i18n, home pública, primitivos | `frontend-surfaces` |
| página / formulário de login | `frontend-login` + `frontend-surfaces` |
| shell autenticado, sidebar, UserMenu | `frontend-shell` + `frontend-surfaces` |
| chat de produto (lista + thread) | `frontend-chat` + `frontend-shell` + `frontend-surfaces` |
| inbox / fila na UI | `frontend-backoffice` + `frontend-shell` + `ops-backoffice` + `frontend-surfaces` |

- `name` ou `description` cobre o recorte → **é a skill**.
- Duas candidatas → leia as duas; fique com a do recorte.
- Nenhuma → diga em uma frase e implemente só com o que o repo já faz.
- Kit novo: **uma linha nesta tabela**. Rule nova por kit é over. `architecture` «Onde mora» mapeia capacidade; não é segundo kit.

Não invente HOW que já tem skill. Não copie o harness para dentro do produto.
Não copie o Superpowers (`using-superpowers`: skill antes de qualquer frase, inclusive pergunta). Aqui a skill entra **antes de editar**; pergunta sem implementação pula este gate.
Entrega: conferência da skill + `/principles-audit` e `/security-audit` até zero achados.

## Exceções (pula Gate 2, não o Gate 1)

- Pergunta sem implementação.
- Skill citada pelo nome — ainda assim leia a `SKILL.md`.
- Typo, rename ou uma linha sem recorte de engenharia.

## Anti-padrão

- Implementar e “ver skill depois”.
- Resumir skill de memória.
- Ignorar skill porque “é mais rápido do meu jeito”.
