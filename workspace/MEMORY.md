# Builder — Long-term Memory

_Durable facts, decisions, and preferences. This file loads at every session start._
_Update this when something is worth remembering across sessions._
_Keep it concise — this is a reference, not a log._

---

## The Human

- **Project:** OpenClaw-based agent platform on Hetzner Ubuntu VPS (ARM64)
- **Preferences:** CLI workflows; check built-in OpenClaw features before external tools
- **Validation rule:** Always send a test message and confirm agent reply before marking work done
- **Commit rule:** After agent creation work — always commit + push to GitHub
- **Auth rule:** Never disclose Doppler secrets in chat. Never suggest Anthropic API keys — OAuth only.
- **Communication style:** Concise. No filler. Opinions welcome.

## Infrastructure

- **3 OpenClaw instances:** openclaw-builder (:18789), openclaw-aivar (:18791), openclaw-lina (:18795)
- **Services run as:** `claude-user`
- **State dirs:** `/home/builder/.openclaw`, `generated_agents/scheduler/.openclaw`, `generated_agents/lina-pm-agent/.openclaw`
- **Doppler service token:** in `/etc/default/openclaw-builder` (root-only, read by systemd)
- **Secrets manager:** Doppler (project: `openclaw-builder`, config: `prd`)
- **Git:** `core.sharedRepository=group` — both Codex and Claude can commit

## Auth

- **Anthropic OAuth token** — refreshed by root cron every 2h; services restarted by healthcheck within 5 min after refresh
- **Refresh script:** `/home/builder/scripts/refresh_anthropic_token.py` — does real OAuth refresh
- **Token source:** `~/.claude/.credentials.json` → `claudeAiOauth.accessToken`
- **Restart trigger:** healthcheck compares `credentials.json` mtime vs service `ActiveEnterTimestamp` — if creds newer → restart
- **If auth fails manually:** `python3 /home/builder/scripts/refresh_anthropic_token.py` then `sudo systemctl restart openclaw-builder && sudo systemctl restart openclaw-aivar && sudo systemctl restart openclaw-lina`
- **Root cause of stale-token bugs:** token-string comparison never detects staleness when cron updates both files simultaneously — mtime check fixes this

## Agents Built

- **Aivar (scheduler):** in `generated_agents/scheduler/` — scheduling + cron agent
- **Lina (PM):** in `generated_agents/lina-pm-agent/` — project management agent

## Security

- No-disclosure policy for Doppler secrets (implemented 2026-02-28)
- Override protocol documented in `SECURITY_OVERRIDE_PROTOCOL.md`

---

_Last updated: 2026-03-02 (fixed stale-token restart logic in healthcheck)_

## Skills Policy (Added 2026-03-02)

- **Only Builder has skills:** builder + doppler
- **Other agents: NO skills** - they use OpenClaw tools only
- **New agents: Start with zero skills** unless explicitly needed
- **Violation response:** Remove immediately, restart agent, commit

## Scheduled Reports

- **Memory Benchmark Report:** Every Friday 09:00 UTC via healthcheck cron
  - Script: `/home/builder/scripts/memory_benchmark.py --compare`
  - Compares pre-memory vs post-memory session metrics
  - Sends Telegram report automatically
  - Documented in: `CLAUDE_CONTEXT_LOG.md` (2026-03-02 entry)

## Domain Configuration

- **Domain:** chuday.eu
- **Reverse Proxy:** Caddy (Docker container: openclaw-caddy-proxy)
- **SSL:** Auto-managed by Caddy (Let's Encrypt)
- **Backend:** OpenClaw gateway on localhost:18789
- **Paths:**
  - `/` → 301 redirect → `/clawagent/`
  - `/clawagent/*` → OpenClaw Control UI
- **Config:** `/home/builder/proxy/Caddyfile`
- **Restart:** `cd /home/builder/proxy && docker-compose restart`

## Subagent Work Tracking

- **Protocol:** `SUBAGENT_PROTOCOL.md`
- **When agents (Lina/Aivar) spawn subagents for Builder work:** They MUST document in `CLAUDE_CONTEXT_LOG.md` and notify Builder
- **Builder workflow:** Check context log at session start for subagent work
- **Example:** Odoo deployment (Mar 5) - done via subagent, now documented
