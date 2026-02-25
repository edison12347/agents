---
name: doppler
description: Manage Builder secrets via Doppler CLI only (no local secret files)
metadata: {"openclaw":{"always":true,"emoji":"🔐","agents":["builder"]}}
---

# Doppler Skill

## When to Activate

- Add or rotate secrets for Builder runtime
- Validate Doppler auth and project/config scope
- Verify required secrets for Telegram, gateway auth, and model providers

## Commands

```bash
doppler me

doppler setup --project openclaw-builder --config prd --scope /home/builder --no-interactive

doppler secrets set OPENCLAW_GATEWAY_TOKEN=<value> --project openclaw-builder --config prd
doppler secrets set TELEGRAM_BOT_TOKEN=<value> --project openclaw-builder --config prd
doppler secrets set TELEGRAM_OWNER_ID=<numeric_id> --project openclaw-builder --config prd
doppler secrets set OPENAI_API_KEY=<value> --project openclaw-builder --config prd
doppler secrets set ANTHROPIC_API_KEY=<value> --project openclaw-builder --config prd

doppler run --project openclaw-builder --config prd -- openclaw channels status --probe
```

## Rules

- Never write secrets to local files
- Use Doppler project/config scope only
- Restart service after secret changes
