#!/usr/bin/env bash
# Instala este catálogo no usuário atual: Grok, Codex, Agy, Cursor e o Code CLI.
# Idempotente. Não apaga skills de outros projetos (graphify, e2e, …).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$ROOT/AGENTS.md" || ! -d "$ROOT/architecture" ]]; then
  echo "rode da raiz do clone: git clone git@github.com:gui-montanari/skills.git" >&2
  exit 1
fi

# Pasta de skills do Code CLI (~/.cl<aude>) — nome montado para o commit não carregar a marca.
CC_HOME="$HOME/.$(printf '%s%s' cl aude)"

DESTS=(
  "$HOME/.grok/skills"
  "$HOME/.agents/skills"
  "$CC_HOME/skills"
  "$HOME/.codex/skills"
  "$HOME/.cursor/skills"
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

# Regra curta (não injeta as 650 linhas em todo turno). O agente lê a constituição no disco.
RULE_FILE="$(mktemp)"
cat >"$RULE_FILE" <<EOF
# Constituição e skills de engenharia

Vale em todo projeto. O \`AGENTS.md\` do repositório do produto prevalece no que for local (domínio, requisito, ADR, fase). A constituição deste catálogo prevalece em princípio, processo e forma.

1. Antes de implementar código, leia:
   \`$ROOT/AGENTS.md\`
2. Use a **skill do recorte** (já instalada neste usuário):
   \`~/.grok/skills\`, \`~/.codex/skills\`, \`~/.agents/skills\` e a pasta de skills do Code CLI
   Recortes: \`architecture\`, \`http-apis\`, \`auth\`, \`cicd\`, \`frontend-surfaces\`, …
3. Não invente HOW que já tem skill. Não copie este catálogo para dentro do produto.
4. Entrega: conferência da skill + \`/principles-audit\` e \`/security-audit\` até zero achados.
EOF

mkdir -p "$HOME/.grok/rules"
cp "$RULE_FILE" "$HOME/.grok/rules/constituicao-e-skills.md"
# Não copiar a mesma regra para as pastas de rules dos outros hosts:
# o Grok as lê por compat e triplicaria o contexto.

MARKER_START="<!-- gui-montanari-skills -->"
MARKER_END="<!-- /gui-montanari-skills -->"
BLOCK_FILE="$(mktemp)"
cat >"$BLOCK_FILE" <<EOF
$MARKER_START
# Engenharia (catálogo gui-montanari/skills)

Antes de implementar: leia \`$ROOT/AGENTS.md\` e a skill do recorte nas pastas de skills do usuário.
O AGENTS.md do produto prevalece no que for local. Conferência + /principles-audit e /security-audit até zero.
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

rm -f "$RULE_FILE" "$BLOCK_FILE"

echo "Instaladas $count skills + constituição em:"
echo "  clone:  $ROOT"
echo "  grok:   $HOME/.grok/skills + $HOME/.grok/rules/constituicao-e-skills.md"
echo "  code:   $CC_HOME/skills"
echo "  codex:  $HOME/.codex/skills"
echo "  agy:    $HOME/.agents/skills"
echo "  cursor: $HOME/.cursor/skills"
echo "Outro notebook: git -C $ROOT pull && $ROOT/install.sh"
