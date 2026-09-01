#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/bin" "$HOME/.config/mcp-cli-toolkit/secrets" "$HOME/.config/mcp-cli-toolkit/selections"
python3 "$ROOT/scripts/migrate-selections.py"
python3 -m venv "$ROOT/mcp_servers/azure/.venv"
"$ROOT/mcp_servers/azure/.venv/bin/pip" install -q -r "$ROOT/mcp_servers/azure/requirements.txt"
npm install --prefix "$ROOT/mcp_servers/gdrive"
chmod +x "$ROOT"/wrappers/* "$ROOT"/scripts/*.sh "$ROOT/mcp_toolkit.py" "$ROOT/mcp_servers/gdrive/start.sh"
for wrapper in claude-cli codex-cli opencode-cli agy-cli grok-cli cursor-cli; do
  ln -sfn "$ROOT/wrappers/$wrapper" "$HOME/bin/$wrapper"
done
echo "Instalação concluída. Configure os segredos conforme GUIDE.md."
