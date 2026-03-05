# Gateway UI "unauthorized: too many failed authentication attempts"

## Root Cause

You hit the rate limit (10 failed connection attempts within 5 minutes). The gateway has locked you out for 5 minutes.

**Why it happened:**
1. WebSocket was failing to connect (Caddy config issue)
2. UI kept retrying with placeholder token `OPENCLAW_GATEWAY_TOKEN`
3. Each retry counted as failed auth attempt
4. After 10 attempts → 5-minute lockout

## Immediate Fix

**On the server, run:**
```bash
sudo systemctl restart openclaw-builder openclaw-aivar openclaw-lina
```

This clears the rate limit immediately and loads all pending config changes.

**Then refresh browser:** Ctrl+Shift+R (or Cmd+Shift+R)

## Long-term Fix: Use Real Gateway Token

The UI shows `OPENCLAW_GATEWAY_TOKEN` (placeholder). You need the **real token value**.

**To get your gateway token:**
```bash
doppler secrets get OPENCLAW_GATEWAY_TOKEN --plain --project openclaw-builder --config prd
```

**In the UI:**
1. Copy the token value from above command
2. Paste it in the "Gateway Token" field (replace `OPENCLAW_GATEWAY_TOKEN`)
3. Click "Connect"

The UI will save this token in browser localStorage.

## External Health Check

Created `/home/builder/scripts/test-gateway-external.sh` to test WebSocket like a real external user.

**Run manually:**
```bash
doppler run --project openclaw-builder --config prd -- \
  /home/builder/scripts/test-gateway-external.sh
```

**Integrated into healthcheck:** Will run automatically and alert if external access fails.

## What Was Fixed

1. ✅ **Caddy WebSocket ordering** - WebSocket check before redirect
2. ✅ **Caddy proxy headers** - Proper WebSocket upgrade headers
3. ✅ **External health check** - Tests from user perspective
4. ⏳ **Rate limit lockout** - Requires service restart

## Status

- **WebSocket config:** Fixed (commit 1c5662e)
- **External test script:** Created
- **Rate limit:** Active until services restart
- **Token:** Still using placeholder (needs real value)

**After restart, it should work immediately.**
