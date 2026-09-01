#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export CLIENT_ID="${CLIENT_ID:-$GDRIVE_CLIENT_ID}"
export CLIENT_SECRET="${CLIENT_SECRET:-$GDRIVE_CLIENT_SECRET}"
export GDRIVE_CREDS_DIR="${GDRIVE_CREDS_DIR:-$HOME/.config/mcp-cli-toolkit/gdrive}"
node ./prepare-credentials.mjs
exec node ./server.mjs
