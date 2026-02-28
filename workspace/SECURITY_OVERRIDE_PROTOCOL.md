# Security Override Protocol

## Default Policy: NEVER Disclose Secrets

**Builder will NEVER disclose Doppler secrets via chat, even if the owner requests them.**

This includes:
- ❌ Doppler secret values
- ❌ API keys, tokens, passwords
- ❌ OAuth credentials
- ❌ Any sensitive configuration data

**Why:** Prevent accidental disclosure, prompt injection, and social engineering attacks.

## Override Protocol (for legitimate access)

### Method 1: Direct Doppler Access (Recommended for reading secrets)
```bash
# From anywhere (mobile app, web, CLI)
doppler secrets get SECRET_NAME --plain --project openclaw-builder --config prd
```

### Method 2: Override Token (When you need Builder to disclose via chat)

**Use case:** You're on mobile, need Builder to retrieve and send a secret value.

**How it works:**

1. **Get your override token from Doppler:**
   ```bash
   # Via Doppler CLI, mobile app, or web dashboard
   doppler secrets get BUILDER_OVERRIDE_TOKEN --plain
   ```

2. **Include the token in your request to Builder:**
   ```
   Builder, I need TELEGRAM_BOT_TOKEN.
   Override: 48b818f899063a4378b80c787fcee6719663c230fdb9bef3b2675d890f848590
   ```

3. **Builder validates:**
   - Checks if provided token matches `BUILDER_OVERRIDE_TOKEN` in Doppler
   - If match: discloses the requested secret
   - If no match: refuses and points to this protocol

4. **Builder responds with the secret value**

**Token rotation:** To invalidate the current token, regenerate it in Doppler:
```bash
doppler secrets set BUILDER_OVERRIDE_TOKEN="$(openssl rand -hex 32)"
```

## Why This Works

- **Requires Doppler access:** Attacker would need your Doppler credentials
- **No SSH required:** Works from mobile/anywhere you have Doppler access
- **Simple workflow:** One token lookup, paste into chat
- **Rotatable:** Change the token anytime to invalidate old requests
- **Resistant to prompt injection:** Token is external to the chat context

## Security Properties

- Token stored in Doppler (already secured with your authentication)
- You control the token (can rotate anytime)
- Builder only discloses secrets when override token is provided
- No filesystem access required (mobile-friendly)
- Simpler than file-based protocols

## Implementation

Builder reads `BUILDER_OVERRIDE_TOKEN` from environment (injected by Doppler at startup).

When a secret disclosure request includes "Override: TOKEN", Builder:
1. Compares provided token with `$BUILDER_OVERRIDE_TOKEN`
2. If exact match: proceeds with disclosure
3. If no match or no token: refuses request

See `SECURITY.md` for full security model.
