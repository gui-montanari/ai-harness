#!/usr/bin/env bash
# Instala o harness neste usuário: skills, rules, hooks, subagents e MCP da máquina.
# Idempotente. Não apaga overlay local (stockfy-repos-autorizacao, hooks de cliente, …).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANON="$HOME/.local/share/ai-harness"

if [[ ! -f "$ROOT/AGENTS.md" || ! -d "$ROOT/architecture" || ! -d "$ROOT/rules" || ! -d "$ROOT/hooks" || ! -d "$ROOT/mcp" || ! -d "$ROOT/subagents" ]]; then
  echo "rode da raiz do clone: git clone git@github.com:gui-montanari/ai-harness.git" >&2
  exit 1
fi

# Pasta de skills do Code CLI (~/.cl<aude>) — nome montado para o commit não carregar a marca.
CC_HOME="$HOME/.$(printf '%s%s' cl aude)"

if [[ "$ROOT" != "$CANON" ]]; then
  mkdir -p "$(dirname "$CANON")"
  ln -sfn "$ROOT" "$CANON"
fi

DESTS=(
  "$HOME/.grok/skills"
  "$HOME/.agents/skills"
  "$CC_HOME/skills"
  "$HOME/.codex/skills"
  "$HOME/.cursor/skills"
  "$HOME/.gemini/config/skills"
  "$HOME/.gemini/skills"
  "$HOME/.codeium/windsurf/skills"
  "$HOME/.config/opencode/skills"
)

for dest in "${DESTS[@]}"; do
  mkdir -p "$dest"
done

count=0
while IFS= read -r -d '' f; do
  d="$(dirname "$f")"
  name="$(basename "$d")"
  for dest in "${DESTS[@]}"; do
    ln -sfn "$d" "$dest/$name"
  done
  count=$((count + 1))
done < <(find "$ROOT/architecture" "$ROOT/backend" "$ROOT/frontend" "$ROOT/quality" -name SKILL.md -print0)

# Agent Skills oficiais do Make (MIT, integromat/make-skills). Não são HOW deste harness.
# Cache na máquina; symlink só no Cursor e no protocolo Open Agent Skills — não no Grok,
# para o HOW hexagonal ganhar quando o recorte é adapter de produto.
MAKE_SKILLS_CACHE="$HOME/.local/share/make-skills"
make_skill_count=0
mkdir -p "$(dirname "$MAKE_SKILLS_CACHE")"
if [[ -d "$MAKE_SKILLS_CACHE/.git" ]]; then
  if ! git -C "$MAKE_SKILLS_CACHE" fetch --depth 1 origin || ! git -C "$MAKE_SKILLS_CACHE" reset --hard FETCH_HEAD; then
    echo "aviso: Make Agent Skills não atualizadas (rede ou git). Ponte make-scenarios continua." >&2
  fi
elif ! git clone --depth 1 https://github.com/integromat/make-skills.git "$MAKE_SKILLS_CACHE"; then
  echo "aviso: Make Agent Skills não clonadas (rede ou git). Ponte make-scenarios continua." >&2
fi
if [[ -f "$MAKE_SKILLS_CACHE/skills.publish.json" ]]; then
  mkdir -p "$HOME/.cursor/skills" "$HOME/.agents/skills"
  while IFS= read -r skill_name; do
    [[ -n "$skill_name" ]] || continue
    src="$MAKE_SKILLS_CACHE/skills/$skill_name"
    [[ -f "$src/SKILL.md" ]] || continue
    ln -sfn "$src" "$HOME/.cursor/skills/$skill_name"
    ln -sfn "$src" "$HOME/.agents/skills/$skill_name"
    make_skill_count=$((make_skill_count + 1))
  done < <(python3 -c "import json,sys; print('\n'.join(json.load(open(sys.argv[1]))))" "$MAKE_SKILLS_CACHE/skills.publish.json")
fi

# Rules: catálogo em $ROOT/rules + overlay em ~/.config/ai-harness/overlay/rules.
# Grok lê só ~/.grok/rules (compat vendor off). Codex/Agents recebem o corpo em AGENTS.md.
python3 "$ROOT/rules/sync.py"
rule_count="$(python3 -c "import importlib.util; from pathlib import Path; p=Path('$ROOT/rules/sync.py'); s=importlib.util.spec_from_file_location('rs', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.catalog()))")"

# Hooks: um catálogo, adapters por host (Grok, Cursor, Claude, Antigravity, Gemini, Windsurf).
# Overlay de cliente: ~/.config/ai-harness/overlay/hooks/ — o sync não apaga o que não é gerido.
python3 "$ROOT/hooks/sync.py"
hook_count="$(python3 -c "import importlib.util; from pathlib import Path; p=Path('$ROOT/hooks/sync.py'); s=importlib.util.spec_from_file_location('hs', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.catalog()))")"

# Subagents: papéis no host (Cursor / Claude). Overlay em ~/.config/ai-harness/overlay/subagents/.
python3 "$ROOT/subagents/sync.py"
agent_count="$(python3 -c "import importlib.util; from pathlib import Path; p=Path('$ROOT/subagents/sync.py'); s=importlib.util.spec_from_file_location('ags', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.catalog()))")"

MCP="$ROOT/mcp"
mkdir -p "$HOME/bin" "$HOME/.config/ai-harness/secrets" "$HOME/.config/ai-harness/selections"
python3 "$MCP/scripts/migrate-selections.py"
legacy_secrets="$HOME/.config/mcp-cli-toolkit/secrets"
if [[ -d "$legacy_secrets" ]]; then
  for src in "$legacy_secrets"/*.env; do
    [[ -f "$src" ]] || continue
    dest="$HOME/.config/ai-harness/secrets/$(basename "$src")"
    if [[ ! -f "$dest" ]]; then
      cp "$src" "$dest"
      chmod 600 "$dest"
    fi
  done
fi
for example in "$MCP"/secrets.example/*.env.example; do
  [[ -f "$example" ]] || continue
  dest="$HOME/.config/ai-harness/secrets/$(basename "$example" .example)"
  if [[ ! -f "$dest" ]]; then
    cp "$example" "$dest"
    chmod 600 "$dest"
  fi
done
chmod +x "$MCP"/wrappers/* "$MCP"/scripts/* "$MCP/mcp_toolkit.py" "$MCP/mcp_servers/gdrive/start.sh" 2>/dev/null || true
if [[ -f "$MCP/mcp_servers/gdrive/package-lock.json" ]]; then
  (cd "$MCP/mcp_servers/gdrive" && npm ci --omit=dev)
fi
if [[ -f "$MCP/mcp_servers/hostinger/package-lock.json" ]]; then
  (cd "$MCP/mcp_servers/hostinger" && npm ci --omit=dev)
fi
for wrapper in claude-cli codex-cli opencode-cli agy-cli grok-cli cursor-cli; do
  ln -sfn "$MCP/wrappers/$wrapper" "$HOME/bin/$wrapper"
done
python3 "$MCP/scripts/repair_npx_shebang_bins.py"
python3 "$MCP/mcp_toolkit.py" sync --client all --profile default
mcp_count="$(python3 -c "import importlib.util; from pathlib import Path; p=Path('$MCP/mcp_toolkit.py'); s=importlib.util.spec_from_file_location('mt', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.catalog()))")"

echo "Instaladas $count skills + $make_skill_count Make Agent Skills (Cursor/.agents, cache $MAKE_SKILLS_CACHE) + $rule_count rules + $hook_count hooks + $agent_count subagents + $mcp_count MCP(s) (catálogo+overlay) + constituição em:"
echo "  clone:  $ROOT  (canônico: $CANON)"
echo "  hosts:  grok, cursor, claude, subagents, codex, gemini/antigravity, windsurf, opencode"
echo "  overlay: $HOME/.config/ai-harness/overlay/{rules,hooks,mcp,subagents} (opcional, não vai no git público)"
echo "  secrets: $HOME/.config/ai-harness/secrets/*.env"
echo "Outro notebook: git clone git@github.com:gui-montanari/ai-harness.git ~/projetos/ferramentas/ai-harness && ~/projetos/ferramentas/ai-harness/install.sh"
