#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/mcp_toolkit.py" doctor --profile "${MCP_PROFILE:-default}" "$@"
