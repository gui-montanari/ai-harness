#!/bin/bash
# Compat: o install canônico é o da raiz do harness.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
exec "$ROOT/install.sh"
