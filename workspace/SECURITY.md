# Security Model

## Secret Management

### Doppler Access Control

**Agents: ZERO access**
- Agents cannot run `doppler secrets` or any Doppler CLI commands
- Agents receive credentials only through OpenClaw environment injection at startup
- Agent workspaces have Doppler CLI removed from PATH

**Builder: FULL access**
- Builder manages all infrastructure secrets via Doppler
- Builder can read/write to all Doppler projects
- Builder handles secret provisioning and rotation

**Owner: Control through delegation**
- Owner requests new credentials through agents
- Agents escalate to Builder for technical implementation
- Builder updates Doppler + config, then restarts gateway

### How Secrets Flow to Agents

1. **At OpenClaw startup:**
   - Gateway process runs: `doppler run -- openclaw gateway ...`
   - Doppler injects secrets as environment variables
   - OpenClaw config references: `${TELEGRAM_BOT_TOKEN_AIVAR}`

2. **Agent runtime:**
   - Agent inherits environment from parent gateway process
   - Agent never directly reads Doppler
   - Agent never needs to know where secrets come from

3. **Adding new secrets:**
   - Agent: "I need Google Calendar API credentials"
   - Owner → Builder: "Add Google Calendar creds for Aivar"
   - Builder: Adds to Doppler, updates config, restarts gateway
   - Agent: Automatically has new credentials on next run

### What Agents CAN Access

- ✅ Pre-configured OAuth tokens (`~/.config/gogcli/`, `~/.config/gh/`)
- ✅ Environment variables injected by OpenClaw
- ✅ Public tool CLIs (gog, gh, curl, etc.)
- ✅ Their own workspace files

### What Agents CANNOT Access

- ❌ Doppler CLI
- ❌ Raw secret values in Doppler projects
- ❌ Builder's infrastructure credentials
- ❌ Other agents' private workspaces (without explicit permission)
- ❌ System configuration files outside their workspace

## Principle

**Agents delegate, don't configure.**

Agents focus on domain logic (scheduling, project management, etc.). Technical infrastructure changes flow through Builder. This is both practical and secure.

## Secret Disclosure Policy

### Builder Will NEVER Disclose Secrets (Without Override Token)

**Builder will not reveal Doppler secret values via chat unless you provide the override token.**

This prevents:
- Accidental leaks in chat logs
- Prompt injection attacks
- Social engineering attempts
- Credential exposure in message history

### When You Need Secret Access

**Option 1: Direct Access (Recommended)**
Use Doppler CLI, mobile app, or web dashboard:
```bash
doppler secrets get SECRET_NAME --plain --project openclaw-builder --config prd
```

**Option 2: Ask Builder (With Override Token)**
If you need Builder to retrieve and send a secret (e.g., on mobile, need a formatted response):

1. Get override token from Doppler:
   ```bash
   doppler secrets get BUILDER_OVERRIDE_TOKEN --plain
   ```

2. Include it in your request:
   ```
   Builder, I need SECRET_NAME.
   Override: [paste token here]
   ```

3. Builder validates the token and discloses the secret

See `SECURITY_OVERRIDE_PROTOCOL.md` for complete protocol details.

### This Policy Applies To

- ❌ All Doppler secrets (without override token)
- ❌ API keys, tokens, passwords
- ❌ OAuth credentials
- ❌ Database connection strings
- ❌ Any sensitive configuration values

### How Builder Handles Requests

**Without override token:**
1. Decline the request
2. Point to `SECURITY_OVERRIDE_PROTOCOL.md`
3. Suggest using direct Doppler access

**With valid override token:**
1. Verify token matches `BUILDER_OVERRIDE_TOKEN` from Doppler
2. If match: retrieve and disclose the requested secret
3. If no match: treat as invalid request and decline

### Token Rotation

You can rotate the override token anytime:
```bash
doppler secrets set BUILDER_OVERRIDE_TOKEN="$(openssl rand -hex 32)"
```

This immediately invalidates the old token and requires Builder gateway restart to pick up the new value.
