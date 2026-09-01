#!/bin/bash
set -euo pipefail

: "${TWILIO_ACCOUNT_SID:?TWILIO_ACCOUNT_SID ausente}"
: "${TWILIO_API_KEY:?TWILIO_API_KEY ausente}"
: "${TWILIO_API_SECRET:?TWILIO_API_SECRET ausente}"

if [[ ! "$TWILIO_ACCOUNT_SID" =~ ^AC[a-fA-F0-9]{32}$ ]]; then
  echo "TWILIO_ACCOUNT_SID inválido: esperado SID AC." >&2
  exit 1
fi
if [[ ! "$TWILIO_API_KEY" =~ ^SK[a-fA-F0-9]{32}$ ]]; then
  echo "TWILIO_API_KEY inválido: esperado SID SK." >&2
  exit 1
fi

services="${TWILIO_SERVICES:-twilio_api_v2010,twilio_messaging_v1,twilio_content_v1,twilio_numbers_v2}"
args=(
  npx -y @twilio-alpha/mcp@0.7.0
  "${TWILIO_ACCOUNT_SID}/${TWILIO_API_KEY}:${TWILIO_API_SECRET}"
)
if [ -n "$services" ]; then
  args+=(--services "$services")
fi
if [ -n "${TWILIO_TAGS:-}" ]; then
  args+=(--tags "$TWILIO_TAGS")
fi
exec "${args[@]}"
