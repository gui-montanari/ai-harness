---
name: client-harness
description: >
  Use when creating a private per-client harness (stockfy-harness, tenda-harness),
  moving client skills/rules/hooks/MCP out of ai-harness, installing overlay, or
  when the user mentions client-harness, overlay de cliente, /client-harness.
  Not mcp-servers (product MCP). Not git-activity (worktree/PR).
---

# Harness de cliente

**REQUIRED BACKGROUND:** constituição `AGENTS.md` (overlay fora do git público).
Esta skill é o HOW de um **repositório privado irmão** do `ai-harness`.

`ai-harness` = constituição + HOW universal. Cliente **não** entra lá (subpasta é violação de SRP). Skill de cliente em `~/.grok/skills` vaza para os outros clientes.

## Forma

Repo **privado**. Clone ao lado do harness universal:

```text
~/projetos/ferramentas/ai-harness/
~/projetos/ferramentas/{cliente}-harness/
```

```text
{cliente}-harness/
  AGENTS.md          # coordenação do cliente (repos, produção, nome de branch)
  install.sh         # projeta overlay + skills do workspace
  rules/             # gates só deste cliente (autorização de repo alheio, …)
  hooks/             # catalog.json + scripts/
  mcp/               # catalog.json só dos servidores deste cliente + código
  skills/            # debug, deploy, domínio — NÃO globais
```

Segredo continua em `~/.config/ai-harness/secrets/*.env`. OAuth em `~/.mcp-auth`. Nem um nem outro neste git.

MCP/hook/rule que é **só desta máquina** e de vários clientes (VPS, AWS pessoal) permanece no overlay local, fora de qualquer `{cliente}-harness`.

## install.sh (contrato)

1. **Rules/hooks/MCP → overlay por merge.** Escreve em `~/.config/ai-harness/overlay/{rules,hooks,mcp}/`. Upsert das chaves deste cliente. **Não** apaga entradas de outro cliente nem do overlay de máquina.
2. **Skills → workspace do cliente, nunca `~/.grok/skills`.** Symlink `skills/` para `~/projetos/{cliente}/.agents/skills` e para o repo de produto principal (`…/{produto}/.agents/skills`), para o Grok achar com CWD no git do produto.
3. Chama `~/projetos/ferramentas/ai-harness/install.sh` no fim, para projetar overlay nos hosts.
4. Idempotente. Sem `.venv` nem `__pycache__` no git.

Notebook novo:

```bash
git clone git@github.com:gui-montanari/ai-harness.git ~/projetos/ferramentas/ai-harness
~/projetos/ferramentas/ai-harness/install.sh
git clone git@github.com:gui-montanari/{cliente}-harness.git ~/projetos/ferramentas/{cliente}-harness
~/projetos/ferramentas/{cliente}-harness/install.sh
```

## O que não fazer

- Subpasta `ai-harness/{cliente}/`
- Copiar o harness para dentro do produto
- `ln` de skill de cliente em `~/.grok/skills` / `~/.cursor/skills`
- Rule de cliente no git **público** do `ai-harness`
- Um monorepo “todos os clientes”

Fluxo de worktree/PR: skill `git-activity`. Borda MCP de um **produto**: `mcp-servers` / `mcp-tools`.

## Conferência

Antes de declarar pronto, copie e marque. Caixa vazia = falta.

- [ ] Repo privado; não é subpasta do `ai-harness`
- [ ] Skills só no workspace do cliente; `~/.grok/skills` sem pasta deste cliente
- [ ] Overlay merge (outro cliente / VPS intactos)
- [ ] Segredo fora do git; `install.sh` idempotente
- [ ] `./install.sh` + `ai-harness/install.sh` projetam rules/hooks/MCP nos hosts
