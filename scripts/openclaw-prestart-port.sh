#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-18789}"
TIMEOUT_SEC="${2:-8}"

pids="$(ss -ltnp "sport = :${PORT}" 2>/dev/null | awk -F'pid=' 'NF>1{split($2,a,","); print a[1]}' | sort -u | tr '\n' ' ')"

if [[ -z "${pids// }" ]]; then
  echo "[prestart-port] port ${PORT} is free"
  exit 0
fi

echo "[prestart-port] detected port collision on ${PORT} (pid(s): ${pids})"
for pid in $pids; do
  if [[ "$pid" =~ ^[0-9]+$ ]]; then
    kill -TERM "$pid" 2>/dev/null || true
  fi
done

end=$((SECONDS + TIMEOUT_SEC))
while (( SECONDS < end )); do
  if ! ss -ltn "sport = :${PORT}" | grep -q LISTEN; then
    echo "[prestart-port] port ${PORT} released"
    exit 0
  fi
  sleep 1
done

echo "[prestart-port] port ${PORT} still in use after ${TIMEOUT_SEC}s" >&2
exit 1
