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
Leia a constituição: `~/.local/share/ai-harness/AGENTS.md`.

## Gate 2 — Confirmar skill

Procure a skill do recorte. Não confie na memória. Leia o `SKILL.md` inteiro; não anuncie o nome e siga de memória.

Onde olhar: skills listadas na sessão; `~/.grok/skills/`, `~/.cursor/skills/`,
`~/.codex/skills/`; pasta de skills do Code CLI; e as pastas `skills/` do repo.

**Kit de trabalho** (processo — esta tabela é o dono). Recorte de **produto** (HTTP, auth, fila, UI…): tabela «Selecione as skills» em `architecture`. Não copie produto aqui.

| Trabalho | Ler |
|----------|-----|
| defeito, falha, regressão, teste vermelho | `debug-hypotheses` (evidência de log/Azure: skill de cliente, se houver) |
| worktree, branch, dual delivery, PR | `git-activity` |
| desenhar ou analisar o desenvolvimento | `architecture` — ela puxa o resto pelo que o recorte contém |
| agente, turno, specs, runtime | `agent-orchestration` + `orchestration-runtime` |
| harness de cliente, overlay | `client-harness` |
| auditar o catálogo de skills | `skills-audit` |
| auditar o diff do produto | `principles-audit` + `security-audit` (architecture já manda no gate de entrega) |

- `name` ou `description` cobre o recorte → **é a skill**.
- Duas candidatas → leia as duas; fique com a do recorte.
- Nenhuma → diga em uma frase e implemente só com o que o repo já faz.
- Kit novo: **uma linha nesta tabela** ou na de `architecture`, um dono só. Rule nova por kit é over.

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
