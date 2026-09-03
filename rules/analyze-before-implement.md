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
Leia a constituição: `~/.local/share/ai-harness/AGENTS.md`.

## Gate 2 — Confirmar skill

Procure a skill do recorte. Não confie na memória.

Onde olhar: skills listadas na sessão; `~/.cursor/skills/`, `~/.grok/skills/`,
`~/.codex/skills/`; pasta de skills do Code CLI; e as pastas `skills/` do repo.
Recortes: `architecture`, `http-apis`, `auth`, `cicd`, `frontend-surfaces`, `git-activity`, `client-harness`, …

- `name` ou `description` cobre o recorte → **é a skill**. Leia a `SKILL.md` inteira antes de editar.
- Duas candidatas → leia as duas; fique com a do recorte.
- Nenhuma → diga em uma frase e implemente só com o que o repo já faz.

Não invente HOW que já tem skill. Não copie o harness para dentro do produto.
Entrega: conferência da skill + `/principles-audit` e `/security-audit` até zero achados.

## Exceções (pula Gate 2, não o Gate 1)

- Pergunta sem implementação.
- Skill citada pelo nome — ainda assim leia a `SKILL.md`.
- Typo, rename ou uma linha sem recorte de engenharia.

## Anti-padrão

- Implementar e “ver skill depois”.
- Resumir skill de memória.
- Ignorar skill porque “é mais rápido do meu jeito”.
