# Hooks — enforcement no host

Rule diz o que o modelo deve fazer. Hook **impede** o que o modelo ignoraria.
Só o que é verdade em **qualquer** projeto entra no catálogo.

O desenho é o mesmo do `mcp-cli-toolkit`: **um catálogo agnóstico + adapter por
host**. O `install.sh` chama [`sync.py`](./sync.py). Não se edita JSON de Cursor
ou `settings.json` do Claude na mão.

## Política

| Decisão | Quando |
|---------|--------|
| `deny` | Nunca é acidental: versionar segredo, gravar chave, atribuir commit a Claude/Anthropic, mutar repo Stockfy alheio, push em `stockfy`/`master` |
| `ask` | Destrutivo mas às vezes legítimo, **só no Grok** (`GROK_HOOK_EVENT`). Nos outros hosts vira `deny` (falha fechada) |
| `allow` | Fora do recorte (ex.: `rm -rf` de `tmp` no workspace, `psql -f` de migration, Bash local sem SSH) |

Payload, argv (`git -C`, `sudo`, `&&`) e JSON de decisão vivem em
[`scripts/hooklib.py`](./scripts/hooklib.py). Guards não copiam `jq`.

## Catálogo

[`catalog.json`](./catalog.json) descreve o hook (script, evento, matcher).
[`scripts/`](./scripts/) é a implementação. O sync traduz para o formato de cada
provedor:

| Host | Destino |
|------|---------|
| Grok | `~/.grok/hooks/<nome>.json` |
| Cursor | `~/.cursor/hooks.json` (`beforeShellExecution`) |
| Claude Code | `~/.claude/settings.json` (`hooks`) |
| Antigravity | `~/.gemini/config/hooks.json` |
| Gemini CLI | `~/.gemini/settings.json` (`BeforeTool`) |
| Windsurf / Devin Desktop | `~/.codeium/windsurf/hooks.json` |

O Grok não lê hooks/rules/skills/MCP/`CLAUDE.md` do Claude/Cursor
(`compat.*.{hooks,rules,agents,skills,mcps} = false`) para o mesmo artefato não
rodar duas vezes. Cada host recebe a **própria** projeção do catálogo.

O Grok resolve `command` relativo ao JSON em `~/.grok/hooks/` quando o valor
não é um caminho absoluto. O sync **não** envolve o path em aspas: `" /abs/script.sh"`
vira `~/.grok/hooks/" /abs/script.sh"` e falha com `command not found`.

## Global (neste repo)

| Hook | O que faz |
|------|-----------|
| `protect-secrets` | Recusa `git add`/`commit` de `.env`/credenciais; recusa *escrever* chave (`id_rsa`, `.pem`). `.env` local e `git add .` dependem do `.gitignore` |
| `rm-guard` | Confirma `rm -r -f` em `/`, home, workspace root e árvore de sistema — não em `tmp` do projeto |
| `sql-guard` | Confirma DROP/TRUNCATE/DELETE/UPDATE sem WHERE **só** em cliente de banco (`psql`, `mysql`, …), inclusive `docker exec … psql` |
| `git-destructive-guard` | Confirma `reset --hard`, `push -f` (sem lease), `branch -D`, `clean -f`, discard de `.` |
| `docker-guard` | Confirma `compose down -v`, `volume rm/prune`, `system prune --volumes` |
| `commit-identity-guard` | Recusa trailer `Co-Authored-By`/`Generated-By` Claude ou Anthropic — não a palavra “claude” num path |
| `ssh-prod-guard` | Confirma destrutivo em SSH/MCP de produção; **não** inspeciona Bash local |

## Overlay (não entra neste repo)

Hook de um cliente (`stockfy-foreign-repos`, …) mora em
`~/.config/ai-harness/overlay/hooks/` na máquina:

```text
~/.config/ai-harness/overlay/hooks/
  catalog.json
  scripts/
```

O sync **une** catálogo público + overlay e projeta nos mesmos hosts. O
`install.sh` **não** apaga overlay. Exemplo: [`overlay.example.json`](./overlay.example.json).

## Conferência

- [ ] Mudança de regra: um script no catálogo, não um JSON por IDE
- [ ] `python3 hooks/test_sync.py` verde
- [ ] `python3 -m unittest discover -s hooks/scripts -p 'test_*.py'` verde
- [ ] Overlay: `python3 ~/.config/ai-harness/overlay/hooks/scripts/test_stockfy_git_flow.py` e o unittest do foreign-repos
- [ ] `./install.sh` projeta em todos os hosts da tabela
