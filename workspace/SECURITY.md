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
