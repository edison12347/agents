#!/usr/bin/env bash
set -euo pipefail

RUNTIME_DIR="/home/builder/generated_agents/scheduler/.runtime"
CREDS_PATH="$RUNTIME_DIR/gog-credentials.json"

mkdir -p "$RUNTIME_DIR"

if [[ -z "${GOG_CREDENTIALS_JSON_B64:-}" ]] || [[ "${GOG_CREDENTIALS_JSON_B64}" == "REPLACE_WITH_BASE64_CREDENTIALS_JSON" ]]; then
  echo "[aivar-gog] missing GOG_CREDENTIALS_JSON_B64 in Doppler" >&2
  exit 2
fi

printf '%s' "$GOG_CREDENTIALS_JSON_B64" | base64 -d > "$CREDS_PATH"
chmod 600 "$CREDS_PATH"

echo "[aivar-gog] credentials materialized at $CREDS_PATH"

gog auth credentials "$CREDS_PATH"
if [[ -n "${GOG_ACCOUNT_EMAIL:-}" ]]; then
  gog login "$GOG_ACCOUNT_EMAIL" || true
fi

echo "[aivar-gog] bootstrap complete (if interactive login was required, rerun once after approving in browser)"
