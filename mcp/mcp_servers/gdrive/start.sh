#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export CLIENT_ID="${CLIENT_ID:-$GDRIVE_CLIENT_ID}"
export CLIENT_SECRET="${CLIENT_SECRET:-$GDRIVE_CLIENT_SECRET}"
GDRIVE_CREDS_DIR="${GDRIVE_CREDS_DIR:-$HOME/.config/ai-harness/gdrive}"
legacy_gdrive="$HOME/.config/mcp-cli-toolkit/gdrive"
if [[ ! -d "$GDRIVE_CREDS_DIR" && -d "$legacy_gdrive" ]]; then
  mkdir -p "$GDRIVE_CREDS_DIR"
  cp -a "$legacy_gdrive"/. "$GDRIVE_CREDS_DIR"/
fi
export GDRIVE_CREDS_DIR
node ./prepare-credentials.mjs
exec node ./server.mjs
