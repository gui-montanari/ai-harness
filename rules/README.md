# Rules — gates de processo (sempre ligadas)

Rules não são skills. Skill é o **HOW** de um recorte (`auth`, `http-apis`, …).
Rule é o **gate** que vale em **todo** projeto, **todo** host, **todo** turno.

Fonte única: esta pasta. [`sync.py`](./sync.py) projeta — não se copia o corpo na mão.

## Outro notebook / outro host

```bash
git clone git@github.com:gui-montanari/ai-harness.git ~/projetos/ferramentas/ai-harness
~/projetos/ferramentas/ai-harness/install.sh
```

Um canal nativo por provedor. O Grok **não** varre rules/hooks/skills/MCP/CLAUDE.md de Cursor ou Claude (`compat.*.{rules,hooks,agents,skills,mcps} = false`).

| Host | Como a rule entra |
|------|-------------------|
| Grok | `~/.grok/rules/<nome>.md` |
| Cursor | `~/.cursor/rules/<nome>.mdc` (`alwaysApply`) |
| Claude Code | `~/.claude/rules/<nome>.md` |
| Gemini | `~/.gemini/config/rules/<nome>.md` |
| Codex | corpo concatenado em `~/.codex/AGENTS.md` (Codex não lê `~/.codex/rules`) |
| Agents | corpo concatenado em `~/.agents/AGENTS.md` |

## O que entra aqui (só o global)

Só o que é verdade em **qualquer** repositório desta máquina:

| Arquivo | Gate |
|---------|------|
| [`analyze-before-implement.md`](./analyze-before-implement.md) | Analisar + constituição + skill **antes** de editar |
| [`complete-until-done.md`](./complete-until-done.md) | Não encerrar o turno com trabalho aberto; provar que funciona |
| [`git-discipline.md`](./git-discipline.md) | Commit/push só a pedido; sem skip de hook; sem segredo no git |
| [`git-activity.md`](./git-activity.md) | Atividade a partir da produção, worktree, dual delivery, PR green |

Não entra: HOW de recorte (skill), IDs de um produto, autorização de um cliente, atalho de uma skill de um host (`/graphify`).

Cliente/máquina: `~/.config/ai-harness/overlay/rules/*.md`. O sync une ao catálogo público, migra cópia solta que já estava num host, e **não** apaga overlay. Exemplo: [`overlay.example.md`](./overlay.example.md). O git público não leva isso.

## Frontmatter

Cada `*.md` global (exceto README e `*.example.md`) tem YAML Cursor (`description`, `alwaysApply: true`).
Grok e o Code CLI ignoram o bloco; o modelo lê o corpo.

## Conferência

- [ ] `python3 rules/test_sync.py` verde
- [ ] Quatro gates globais; overlay fora deste repo
- [ ] Grok `compat.cursor` e `compat.claude`: rules/hooks/agents/skills/mcps = false
- [ ] Claude `CLAUDE.md` sem bloco duplicado do harness
