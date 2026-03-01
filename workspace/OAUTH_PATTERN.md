# OAuth Pattern: One-Time Setup, Permanent Access

## Overview

This pattern enables agents to access OAuth-protected services (Gmail, Calendar, etc.) without manual browser authorization on every restart.

**Key principle:** Human authorizes once → refresh token stored in Doppler → agents use non-interactively forever.

## The Pattern

### Phase 1: One-Time Human Authorization (On Laptop/Phone)

1. **Generate OAuth authorization URL**
   ```python
   # Builder generates and sends you a link
   https://accounts.google.com/o/oauth2/auth?client_id=...
   ```

2. **User clicks link, authorizes in browser**
   - Login with service account (e.g., aivar.chudaikin@gmail.com)
   - Click "Allow" to grant permissions
   - Get redirected to `http://localhost/?code=XXXX...`

3. **Exchange authorization code for tokens**
   ```python
   # Builder exchanges code for access_token + refresh_token
   POST https://oauth2.googleapis.com/token
   {
     "code": "4/0AfrIepD...",
     "client_id": "...",
     "client_secret": "...",
     "grant_type": "authorization_code"
   }
   # Returns: access_token, refresh_token, expires_in
   ```

4. **Store refresh token in Doppler**
   ```bash
   # Builder stores as base64-encoded JSON
   doppler secrets set SERVICE_TOKEN_JSON_B64 \
     --value "$(echo '{"email":"...","refresh_token":"..."}' | base64 -w0)"
   ```

### Phase 2: Automated Agent Access (Every Restart)

1. **Bootstrap script runs on agent startup**
   ```bash
   # /home/builder/scripts/agent-service-bootstrap.sh
   # Reads from Doppler, materializes credentials, imports token
   doppler run -- /path/to/bootstrap.sh
   ```

2. **Agent uses service without prompts**
   ```bash
   # gog CLI (or equivalent) auto-refreshes access tokens
   gog gmail messages search "in:inbox"
   # No browser needed - uses refresh token automatically
   ```

## Why This Works Long-Term

### Refresh Token Properties
- ✅ **Doesn't expire** (unless revoked or unused for 6+ months)
- ✅ **Can generate new access tokens** indefinitely
- ✅ **Survives restarts** (stored in Doppler, not local filesystem)
- ✅ **Works across machines** (Doppler is cloud-based)

### Auto-Refresh Mechanism
- Access tokens expire every ~1 hour
- CLI tools (gog, gh, etc.) detect expiry and auto-refresh
- Refresh token → new access token (transparent to agent)
- No human intervention needed

### Durability
```
User authorizes → Refresh token → Doppler → Agent bootstrap → Non-interactive access
     (once)          (permanent)    (cloud)     (every start)      (automatic)
```

## Applying to New Services

### Example: GitHub OAuth

**1. Generate auth URL (Builder does this):**
```python
params = {
    'client_id': GITHUB_CLIENT_ID,
    'scope': 'repo read:org',
    'redirect_uri': 'http://localhost'
}
url = f'https://github.com/login/oauth/authorize?{urlencode(params)}'
# Send to user
```

**2. User authorizes, sends back code**

**3. Exchange code for token:**
```bash
curl -X POST https://github.com/login/oauth/access_token \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "code=$CODE" \
  -H "Accept: application/json"
```

**4. Store in Doppler:**
```bash
doppler secrets set GITHUB_TOKEN_JSON_B64 \
  --value "$(echo '{"token":"gho_..."}' | base64 -w0)"
```

**5. Bootstrap script:**
```bash
#!/bin/bash
# Import token for gh CLI
echo "$GITHUB_TOKEN_JSON_B64" | base64 -d > /tmp/gh-token.json
gh auth login --with-token < /tmp/gh-token.json
rm /tmp/gh-token.json
```

## Current Implementations

### Google Services (Gmail, Calendar, Drive, etc.)
- **Service:** Google OAuth 2.0
- **Doppler secrets:** `GOG_CREDENTIALS_JSON_B64`, `GOG_TOKEN_JSON_B64`
- **Bootstrap:** `/home/builder/scripts/aivar-gog-bootstrap.sh`
- **Agent:** Aivar (scheduler)
- **Status:** ✅ Working, permanent

### Anthropic Claude
- **Service:** Claude.ai OAuth
- **Credentials:** `~/.claude/.credentials.json`
- **Refresh script:** `/home/builder/scripts/refresh_anthropic_token.py`
- **Agents:** Builder, Lina, Aivar
- **Status:** ✅ Working, requires periodic refresh (~4 hours)

## Security Model

### What's Stored in Doppler
- ✅ Client credentials (OAuth app ID/secret)
- ✅ Refresh tokens (long-lived, auto-renewing)
- ❌ Access tokens (ephemeral, auto-generated)

### What's on Disk (Temporary)
- Bootstrap scripts materialize tokens to `/tmp/` during startup
- Immediately imported by CLI tool (gog, gh, etc.)
- Temp files deleted after import
- CLI tools store tokens in `~/.config/` (readable only by agent user)

### What Agents See
- ✅ Working service access (can read Gmail, etc.)
- ❌ Raw Doppler secrets (blocked by security policy)
- ❌ Client credentials (only Builder has access)

## Troubleshooting

### "No accounts configured"
**Cause:** Bootstrap script didn't run or failed
**Fix:** 
```bash
doppler run --project PROJECT --config prd -- /path/to/bootstrap.sh
```

### "Token expired" or "Invalid credentials"
**Cause:** Refresh token was revoked or deleted
**Fix:** Re-run one-time authorization (Phase 1)

### "OAuth token has expired" (Anthropic-specific)
**Cause:** Anthropic tokens expire every ~4 hours
**Fix:**
```bash
python3 /home/builder/scripts/refresh_anthropic_token.py
sudo systemctl restart openclaw-*
```
**Note:** Consider adding a cron job for automatic refresh

### Service-specific token check
```bash
# Google services
gog auth list

# GitHub
gh auth status

# Anthropic
cat ~/.claude/.credentials.json | jq -r '.claudeAiOauth.accessToken' | head -c 20
```

## Best Practices

### For Builder (When Adding New OAuth Services)

1. **Document required scopes** in agent README
2. **Create bootstrap script** following the pattern above
3. **Test non-interactive flow** before marking complete
4. **Store credentials in Doppler** with descriptive names
5. **Add to service restart scripts** (systemd, etc.)

### For User (When Authorizing New Services)

1. **Use the correct account** (check email in authorization prompt)
2. **Verify all requested permissions** before clicking "Allow"
3. **Copy the full redirect URL** (including code parameter)
4. **Confirm token storage** with Builder before testing

### For Agents (Automatic)

- Agents never see raw refresh tokens
- Bootstrap runs via systemd `ExecStartPre` hook
- Tokens materialized just-in-time, cleaned up after import
- No manual intervention needed after initial setup

## Future Enhancements

- [ ] Add OAuth refresh monitoring (alert if token becomes invalid)
- [ ] Centralize bootstrap pattern into reusable script template
- [ ] Document token rotation procedure (when security requires it)
- [ ] Add health check for OAuth token validity

## References

- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- GitHub OAuth: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
- Doppler CLI: https://docs.doppler.com/docs/cli
- gog CLI: https://github.com/autonia/gog
