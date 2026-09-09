# Subagents — papéis despachados pelo host (Cursor / Claude)

Skill é o **HOW** de um recorte. Subagent é um **papel** que o host despacha
(Task): um `.md` com frontmatter `name` + `description`.

Fonte única: esta pasta. [`sync.py`](./sync.py) projeta — não se copia o
corpo na mão para `~/.cursor/agents` ou `~/.claude/agents`.

O Cursor rotula `~/.cursor/agents` como **User**. Isso é o rótulo da pasta
do host, não um segundo catálogo. O SSOT continua aqui.

## Outro notebook / outro host

```bash
git clone git@github.com:gui-montanari/ai-harness.git ~/projetos/ferramentas/ai-harness
~/projetos/ferramentas/ai-harness/install.sh
```

| Host | Como o subagent entra |
|------|----------------------|
| Cursor | `~/.cursor/agents/<nome>.md` |
| Claude Code | `~/.claude/agents/<nome>.md` |

Só o que é verdade em **qualquer** repositório desta máquina entra aqui
(papéis FastAPI universais). Plugin de marketplace (Cursor Team Kit,
Hostinger) **não** se copia — o plugin já é o dono. Subagent de um
**produto** (OracleProphet, Stockfy) mora no overlay ou no repo do produto
(`.cursor/agents` daquele git), não neste git público.

Cliente/máquina: `~/.config/ai-harness/overlay/subagents/*.md`. O sync une
ao catálogo público, migra `overlay/agents` legado e cópia solta que já
estava num host, e **não** apaga overlay. Exemplo:
[`overlay.example.md`](./overlay.example.md).

## Conferência

- [ ] `python3 subagents/test_sync.py` verde
- [ ] Overlay fora deste repo; plugin de IDE não vendorizado aqui
- [ ] Produto específico não entra no git público
