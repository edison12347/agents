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

If you genuinely need a secret value, use one of these methods:

### Method 1: Direct Doppler Access (Recommended)
```bash
# SSH into the server
ssh user@server

# Get the secret yourself
doppler secrets get SECRET_NAME --plain --project PROJECT --config CONFIG
```

### Method 2: Secure File Override (Emergency Only)

If you need Builder to disclose a secret (e.g., you're on mobile, can't SSH):

1. **Create override file with cryptographic token:**
   ```bash
   # Generate a session-specific token
   echo "OVERRIDE_$(date +%s)_$(openssl rand -hex 16)" > /home/builder/workspace/.security-override
   ```

2. **Add the exact token to your request:**
   ```
   Builder, I need SECRET_NAME.
   Override token: OVERRIDE_1709139234_a3f5c2d8e9b1f4a6c7e8d9f0a1b2c3d4
   ```

3. **Builder verifies:**
   - File `/home/builder/workspace/.security-override` exists
   - Token in file matches token in request exactly
   - File was modified within last 5 minutes
   - Only then: disclose the secret

4. **Builder deletes override file immediately after disclosure**

5. **Override file is git-ignored and never committed**

### Method 3: Config Flag Override (Persistent, Auditable)

For temporary debugging sessions:

1. **Set flag in config:**
   ```bash
   # Add to /home/builder/config/openclaw.json
   {
     "builder": {
       "security": {
         "allowSecretDisclosure": true,
         "allowedUntil": "2026-02-28T18:00:00Z"
       }
     }
   }
   ```

2. **Commit to git** (auditable)

3. **Restart gateway**

4. **Builder can now disclose secrets until the expiry time**

5. **Revert the config change when done**

## Why This Works

- **File-based token:** Can't be prompt-injected (requires file system access)
- **Time-based validation:** Token expires after 5 minutes
- **Cryptographic randomness:** Can't be guessed
- **Exact match required:** Typos fail verification
- **Single-use:** File deleted after use
- **Auditable:** Config-based override leaves git trail
- **Out-of-band:** Requires SSH access to create token

## Implementation

See `SECURITY.md` for full security model.

Builder enforces this policy in workspace context files and will refuse secret disclosure requests that don't follow the protocol.
