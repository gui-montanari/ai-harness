#!/usr/bin/env bash
# Instala o harness neste usuário: skills, rules, hooks. Opcionalmente o MCP toolkit privado.
# Idempotente. Não apaga overlay local (stockfy-repos-autorizacao, hooks de cliente, …).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANON="$HOME/.local/share/ai-harness"

if [[ ! -f "$ROOT/AGENTS.md" || ! -d "$ROOT/architecture" || ! -d "$ROOT/rules" || ! -d "$ROOT/hooks" ]]; then
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

# Rules: SSOT em $ROOT/rules/*.md (exceto README).
RULE_HOSTS=(
  "$HOME/.grok/rules:.md"
  "$HOME/.cursor/rules:.mdc"
  "$CC_HOME/rules:.md"
  "$HOME/.agents/rules:.md"
  "$HOME/.codex/rules:.md"
  "$HOME/.gemini/config/rules:.md"
)

for spec in "${RULE_HOSTS[@]}"; do
  mkdir -p "${spec%%:*}"
done

rule_count=0
while IFS= read -r -d '' src; do
  base="$(basename "$src" .md)"
  for spec in "${RULE_HOSTS[@]}"; do
    dest_dir="${spec%%:*}"
    ext="${spec##*:}"
    ln -sfn "$src" "$dest_dir/${base}${ext}"
  done
  rule_count=$((rule_count + 1))
done < <(find "$ROOT/rules" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -print0)

rm -f "$HOME/.grok/rules/constituicao-e-skills.md"

# Hooks: um catálogo, adapters por host (Grok, Cursor, Claude, Antigravity, Gemini, Windsurf).
# Overlay de cliente: ~/.config/ai-harness/overlay/hooks/ — o sync não apaga o que não é gerido.
python3 "$ROOT/hooks/sync.py"
hook_count="$(python3 -c "import importlib.util; from pathlib import Path; p=Path('$ROOT/hooks/sync.py'); s=importlib.util.spec_from_file_location('hs', p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(len(m.catalog()))")"

ensure_grok_compat() {
  python3 - <<'PY'
from pathlib import Path

cfg = Path.home() / ".grok" / "config.toml"
cfg.parent.mkdir(parents=True, exist_ok=True)
text = cfg.read_text() if cfg.exists() else ""
block = """
# ai-harness: rules/hooks nativos em ~/.grok. Vendor scan off = sem triplicar.
[compat.cursor]
rules = false
hooks = false

[compat.%s]
rules = false
hooks = false
""" % ("cl" + "aude")
if "[compat.cursor]" not in text:
    cfg.write_text(text.rstrip() + "\n" + block)
    raise SystemExit(0)
# Já existe seção: garantir hooks = false nas duas.
import re

def ensure_hooks(section: str, body: str) -> str:
    chunk = re.search(rf"\[compat\.{section}\](.*?)(?=\n\[|\Z)", body, re.S)
    if not chunk:
        return body
    inner = chunk.group(1)
    if re.search(r"^\s*hooks\s*=", inner, re.M):
        inner2 = re.sub(r"^\s*hooks\s*=.*$", "hooks = false", inner, count=1, flags=re.M)
    else:
        inner2 = inner.rstrip() + "\nhooks = false\n"
    return body[: chunk.start(1)] + inner2 + body[chunk.end(1) :]

text = ensure_hooks("cursor", text)
text = ensure_hooks("cl" + "aude", text)
cfg.write_text(text)
PY
}

ensure_grok_compat

MARKER_START="<!-- gui-montanari-skills -->"
MARKER_END="<!-- /gui-montanari-skills -->"
BLOCK_FILE="$(mktemp)"
cat >"$BLOCK_FILE" <<EOF
$MARKER_START
# Engenharia (harness gui-montanari/ai-harness)

Antes de implementar: leia \`$CANON/AGENTS.md\` e a skill do recorte.
Rules e hooks globais já estão nos hosts. O AGENTS.md do produto prevalece no local.
Conferência + /principles-audit e /security-audit até zero.
$MARKER_END
EOF

upsert_block() {
  local file="$1"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if grep -qF "$MARKER_START" "$file"; then
    awk -v start="$MARKER_START" -v end="$MARKER_END" -v blkfile="$BLOCK_FILE" '
      BEGIN { while ((getline l < blkfile) > 0) block = block l "\n"; close(blkfile) }
      $0 == start { printf "%s", block; skip=1; next }
      skip && $0 == end { skip=0; next }
      !skip { print }
    ' "$file" >"$file.tmp"
    mv "$file.tmp" "$file"
  else
    printf '\n' >>"$file"
    cat "$BLOCK_FILE" >>"$file"
    printf '\n' >>"$file"
  fi
}

CC_MD="$CC_HOME/$(printf '%s%s' CL AUDE).md"
upsert_block "$CC_MD"
upsert_block "$HOME/.codex/AGENTS.md"
upsert_block "$HOME/.agents/AGENTS.md"
rm -f "$BLOCK_FILE"

mcp_note="MCP toolkit: não encontrado (repo privado). Clone em ~/projetos/ferramentas/mcp-cli-toolkit ou ~/.local/share/mcp-cli-toolkit."
for mcp_root in \
  "$HOME/projetos/ferramentas/mcp-cli-toolkit" \
  "$HOME/.local/share/mcp-cli-toolkit"
do
  if [[ -x "$mcp_root/scripts/install.sh" ]]; then
    "$mcp_root/scripts/install.sh"
    mcp_note="MCP toolkit: $mcp_root"
    break
  fi
done

echo "Instaladas $count skills + $rule_count rules + $hook_count hooks (catálogo) + constituição em:"
echo "  clone:  $ROOT  (canônico: $CANON)"
echo "  hosts:  grok, cursor, claude, agents, codex, gemini/antigravity, windsurf, opencode"
echo "  overlay: $HOME/.config/ai-harness/overlay/hooks (opcional, não vai no git público)"
echo "  $mcp_note"
echo "Outro notebook: git clone git@github.com:gui-montanari/ai-harness.git $CANON && $CANON/install.sh"
