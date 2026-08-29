# skills

Coleção pública de [Agent Skills](https://agentskills.io) para Claude Code, Grok, Codex, Cursor e outros agentes compatíveis.

Cada skill é uma pasta com um `SKILL.md` (metadados + instruções) e, quando necessário, scripts e referências.

## Skills

| Skill | Quando usar |
|-------|-------------|
| [`security-audit`](./security-audit/) | Auditoria de segurança em cinco categorias (isolamento de tenant, autorização só no frontend, IDOR, segredos hardcoded, XSS), com relatório PDF em pt-BR e issues prontas para o GitHub. Comando: `/security-audit` |

## Como usar

Clone o repositório e aponte o agente para a pasta da skill (symlink ou cópia):

```bash
git clone https://github.com/gui-montanari/skills.git
cd skills
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
ln -s "$(pwd)/security-audit" ~/.claude/skills/security-audit
```

Num projeto específico:

```bash
mkdir -p .claude/skills
ln -s /caminho/para/skills/security-audit .claude/skills/security-audit
```

### Grok

```bash
mkdir -p ~/.grok/skills
ln -s "$(pwd)/security-audit" ~/.grok/skills/security-audit
```

### Codex / outros runtimes Agent Skills

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)/security-audit" ~/.agents/skills/security-audit
```

Depois, no chat:

```
/security-audit
```

ou: “Revisa este código atrás de falhas de segurança.”

## Convenção

```
skills/
  <nome-da-skill>/
    SKILL.md          # obrigatório
    scripts/          # opcional
    references/       # opcional
```

`name` no frontmatter YAML deve coincidir com o nome da pasta.

## Licença

MIT. Veja [LICENSE](./LICENSE).
