#!/bin/bash
set -e
env_file="$1"
shift
if [ ! -f "$env_file" ]; then
  echo "Arquivo de segredos ausente: $env_file" >&2
  exit 1
fi
set -a
source "$env_file"
set +a
exec "$@"
