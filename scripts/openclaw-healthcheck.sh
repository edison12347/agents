#!/usr/bin/env bash
set -euo pipefail

LOG_OUT="/home/builder/logs/openclaw-builder.log"
LOG_ERR="/home/builder/logs/openclaw-builder.err.log"
STATE_DIR="/home/builder/logs/.healthcheck"
mkdir -p "$STATE_DIR"

send_alert() {
  local text="$1"
  if [[ -z "${TELEGRAM_OWNER_ID:-}" ]]; then
    echo "[healthcheck] TELEGRAM_OWNER_ID missing; alert not sent: $text" >&2
    return 1
  fi

  openclaw message send \
    --channel telegram \
    --target "$TELEGRAM_OWNER_ID" \
    --message "$text" >/dev/null
}

fingerprint_and_maybe_alert() {
  local kind="$1"
  local details="$2"
  local fp
  fp="$(printf '%s' "$details" | sha256sum | awk '{print $1}')"
  local marker="$STATE_DIR/${kind}-${fp}.sent"
  if [[ -f "$marker" ]]; then
    echo "[healthcheck] duplicate ${kind} alert suppressed"
    return 0
  fi

  send_alert "$details"
  touch "$marker"
}

# 1) gateway health check
if ! openclaw health >/tmp/openclaw-health.out 2>/tmp/openclaw-health.err; then
  msg="⚠️ Builder healthcheck: gateway health failed. Please inspect immediately."
  fingerprint_and_maybe_alert "health" "$msg"
fi

# 2) crash-loop detection (systemd-aware)
if command -v systemctl >/dev/null 2>&1; then
  restarts="$(systemctl show openclaw-builder.service -p NRestarts --value 2>/dev/null || echo 0)"
  if [[ "$restarts" =~ ^[0-9]+$ ]] && (( restarts >= 3 )); then
    msg="⚠️ Builder healthcheck: openclaw-builder.service restart count=${restarts} (possible crash loop)."
    fingerprint_and_maybe_alert "crashloop" "$msg"
  fi
fi

# 3) auth/model failure detection from recent logs
recent="$(tail -n 300 "$LOG_OUT" "$LOG_ERR" 2>/dev/null || true)"
if grep -Eqi "No API key found for provider|all profiles unavailable|Provider .* cooldown|Agent failed before reply" <<<"$recent"; then
  msg="⚠️ Builder healthcheck: detected auth/model failure signatures in recent logs (API key/profile/cooldown)."
  fingerprint_and_maybe_alert "auth" "$msg"
fi

echo "[healthcheck] completed"
