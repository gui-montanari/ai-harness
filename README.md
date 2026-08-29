# skills

Coleção pública de [Agent Skills](https://agentskills.io) para Claude Code, Grok, Codex, Cursor e outros agentes compatíveis.

Cada skill é uma pasta com um `SKILL.md` (metadados + instruções) e, quando necessário, scripts e referências.

**Constituição de desenvolvimento:** [`AGENTS.md`](./AGENTS.md) — SSOT, DRY, KISS, YAGNI, SRP, SOLID, hexagonal, TDD, Docker/CI, limites de tamanho, processo de análise. Copie para a raiz de um produto novo (ou estenda no `AGENTS.md` local).

## Skills

| Skill | Quando usar |
|-------|-------------|
| [`security-audit`](./security-audit/) | Auditoria de segurança em cinco categorias (isolamento de tenant, autorização só no frontend, IDOR, segredos hardcoded, XSS), com relatório PDF em pt-BR e issues prontas para o GitHub. Comando: `/security-audit` |
| [`principios-audit`](./principios-audit/) | Varredura contra o `AGENTS.md`: SSOT, DRY, SRP, hexagonal, TDD, código morto, YAGNI, segurança arquitetural, escala/desacoplamento, auto-recovery de workers. Comandos: `/principios-audit`, `/hexagonal-audit` |

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
ln -s "$(pwd)/principios-audit" ~/.claude/skills/principios-audit
```

### Grok

```bash
mkdir -p ~/.grok/skills
ln -s "$(pwd)/security-audit" ~/.grok/skills/security-audit
ln -s "$(pwd)/principios-audit" ~/.grok/skills/principios-audit
```

### Codex / outros runtimes Agent Skills

```bash
mkdir -p ~/.agents/skills
ln -s "$(pwd)/security-audit" ~/.agents/skills/security-audit
ln -s "$(pwd)/principios-audit" ~/.agents/skills/principios-audit
```

Depois, no chat: `/security-audit`, `/principios-audit` ou `/hexagonal-audit`.

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
