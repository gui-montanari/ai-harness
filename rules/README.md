# Rules — gates de processo (sempre ligadas)

Rules não são skills. Skill é o **HOW** de um recorte (`auth`, `http-apis`, …).
Rule é o **gate** que vale em **todo** projeto, **todo** host, **todo** turno.

Fonte única: esta pasta. `install.sh` só cria symlink — não copia o corpo.

| Destino | Formato | Quem lê |
|---------|---------|---------|
| `~/.grok/rules/<nome>.md` | markdown | Grok (nativo) |
| `~/.cursor/rules/<nome>.mdc` | mesmo arquivo | Cursor IDE |
| pasta de rules do Code CLI | mesmo arquivo | Code CLI |

O Grok, por padrão, também varre `~/.cursor/rules` e a pasta de rules do Code CLI.
O `install.sh` desliga essa varredura (`compat.*.rules = false`) para não
carregar a mesma rule três vezes.

## O que entra aqui (só o global)

Só o que é verdade em **qualquer** repositório desta máquina:

| Arquivo | Gate |
|---------|-------|
| [`analyze-before-implement.md`](./analyze-before-implement.md) | Analisar + constituição + skill **antes** de editar |
| [`complete-until-done.md`](./complete-until-done.md) | Não encerrar o turno com trabalho aberto; provar que funciona |
| [`git-discipline.md`](./git-discipline.md) | Commit/push só a pedido; sem skip de hook; sem segredo no git |

Não entra: HOW de recorte (skill), IDs de um produto, autorização de um cliente.
Esses ficam overlay local (`~/.grok/rules/stockfy-repos-autorizacao.md`, …) —
o `install.sh` **não** apaga.

## Frontmatter

Cada `*.md` (exceto este README) tem YAML Cursor (`description`, `alwaysApply: true`).
Grok e o Code CLI ignoram o bloco; o modelo lê o corpo.

## Outro notebook

```bash
git clone git@github.com:gui-montanari/ai-harness.git ~/.local/share/ai-harness
~/.local/share/ai-harness/install.sh
```
