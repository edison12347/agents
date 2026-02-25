#!/usr/bin/env bash
set -euo pipefail

PROJECT="${1:-openclaw-builder}"
CONFIG="${2:-prd}"

echo "Bootstrapping Doppler placeholders for Builder"
echo "project=${PROJECT} config=${CONFIG}"

doppler --version >/dev/null
doppler me >/dev/null

set_secret() {
  local key="$1"
  local value="$2"
  doppler secrets set "$key=$value" --project "$PROJECT" --config "$CONFIG" >/dev/null
  echo "- ${key} set to placeholder"
}

set_secret "OPENCLAW_GATEWAY_TOKEN" "REPLACE_WITH_64_HEX_TOKEN"
set_secret "TELEGRAM_BOT_TOKEN" "REPLACE_WITH_BOTFATHER_TOKEN"
set_secret "TELEGRAM_OWNER_ID" "REPLACE_WITH_OWNER_NUMERIC_ID"

echo
cat <<MSG
Next steps:
1. Set real values in Doppler:
   doppler secrets set OPENCLAW_GATEWAY_TOKEN=<hex> --project ${PROJECT} --config ${CONFIG}
   doppler secrets set TELEGRAM_BOT_TOKEN=<token> --project ${PROJECT} --config ${CONFIG}
   doppler secrets set TELEGRAM_OWNER_ID=<numeric_id> --project ${PROJECT} --config ${CONFIG}
2. Restart service:
   systemctl restart openclaw-builder.service
3. Verify:
   openclaw channels list
   openclaw channels status --probe
MSG
