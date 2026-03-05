# Shared Context Log

_Bidirectional changelog for infrastructure changes made by Claude Code (server-side AI assistant) and Builder (OpenClaw agent). Both actors should read and write here so neither is blind to what the other has done._

**Claude Code** = the Claude Code CLI session used by Eduard to do server work directly (systemd, scripts, configs, crons)
**Builder** = this OpenClaw agent (Builder👷 on Telegram)

---

## How to use this log

**Claude Code** — write an entry whenever you:
- Create or modify systemd services, cron jobs, scripts
- Change openclaw.json config
- Add/remove sudoers rules
- Create files in /home/builder/workspace or /home/builder/scripts
- Do anything that affects Builder's runtime or the shared server

**Builder** — at the start of each session, `memory_search "CLAUDE_CONTEXT_LOG recent changes"` to catch up. Write an entry when you make server-side changes. Send Eduard a Telegram notification about new Claude Code entries that affect you.

**Format:**
```
## [YYYY-MM-DD] [Actor] — [Title]
**What:** ...
**Why:** ...
**Files:** ...
**Impact:** ...
```

---

## 2026-03-02 Claude Code — Healthcheck rewrite: stop→refresh→start pattern

**What:** Completely rewrote `/home/builder/scripts/openclaw-healthcheck.sh` (twice). Final version uses stop-all-services → run refresh script → start-all-services instead of restart-in-place.

**Why:** Root cause of recurring 401 errors: running OpenClaw services overwrite `auth-profiles.json` with their stale in-memory token on every 401 failure. Any refresh while services are running is immediately undone. Fix: services must be stopped first, then auth-profiles written, then services started fresh.

**Files:** `/home/builder/scripts/openclaw-healthcheck.sh`

**Impact on Builder:** Token rotation is now reliable. Services are stopped for ~5s during rotation (every ~3-4 hours or on mtime change detection). No action needed from Builder.

---

## 2026-03-02 Claude Code — Added "main" agent to token refresh INSTANCES

**What:** Added `"main"` to the agent list in each INSTANCES entry in `/home/builder/scripts/refresh_anthropic_token.py`.

**Why:** `DEFAULT_AGENT_ID = "main"` in OpenClaw source — the "main" auth-profiles acts as a fallback. It was being skipped during refresh, leaving a stale token that could be used as fallback.

**Files:** `/home/builder/scripts/refresh_anthropic_token.py`

**Impact on Builder:** Refresh now covers all auth-profiles paths including the main fallback. No action needed.

---

## 2026-03-02 Claude Code — Removed duplicate cron (claude-user)

**What:** Removed the claude-user crontab which had a duplicate `0 */2 * * *` refresh cron. Only the root cron (same schedule) remains.

**Why:** Two cron runs simultaneously: the second used an already-invalidated refresh token (first run rotated it), causing silent failure and leaving stale tokens.

**Files:** `crontab -r -u claude-user` (no file path; user crontab removed)

**Impact on Builder:** No duplicate refresh races. Healthcheck (root) owns all restarts. No action needed.

---

## 2026-03-02 Claude Code — Moved compaction.memoryFlush to agents.defaults

**What:** Fixed openclaw.json config — moved `compaction.memoryFlush` from `agents.list[0]` (invalid key location) to `agents.defaults` (correct location).

**Why:** OpenClaw was logging "Unrecognized key: agents.list[0].compaction" on startup. The compaction block belongs under defaults, not per-agent overrides.

**Files:** `/home/builder/config/openclaw.json`

**Impact on Builder:** compaction.memoryFlush is now active — before context compaction, you'll get a silent turn to write durable memories. The prompt instructs writing to `memory/YYYY-MM-DD.md` and updating `MEMORY.md`.

---

## 2026-03-02 Claude Code — Enabled memory system for Builder

**What:** Added `memorySearch` config to Builder agent in openclaw.json, downloaded GGUF embedding model (embeddinggemma-300m-qat-Q8_0, 328MB), seeded MEMORY.md with infrastructure facts.

**Why:** Builder had no persistent memory. Every session started cold with no knowledge of prior infrastructure changes.

**Files:**
- `/home/builder/config/openclaw.json` (memorySearch config added to builder agent)
- `/home/builder/workspace/MEMORY.md` (seeded with infrastructure facts)
- GGUF model: `hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf` (downloaded to openclaw cache)
- Memory DB: `/home/builder/.openclaw/memory/builder.sqlite` (created, MEMORY.md indexed)

**Impact on Builder:** Memory search now active. MEMORY.md is watched and auto-indexed. Use `memory_search` at session start for relevant context.

---

## 2026-03-02 Claude Code — Added sudoers rules for openclaw-lina stop/restart

**What:** Added `stop openclaw-lina` and `restart openclaw-lina` to `/etc/sudoers.d/claude-user-systemd`. Previously only `start` was present.

**Why:** Healthcheck stop→refresh→start pattern requires stop and restart permissions for all three services. openclaw-lina was missing stop/restart.

**Files:** `/etc/sudoers.d/claude-user-systemd`

**Impact on Builder:** No direct impact. Lina service is now properly managed by healthcheck.

---

## 2026-03-02 Claude Code — mtime-based restart detection in healthcheck

**What:** Added mtime comparison to healthcheck: if `credentials.json` mtime > service `ActiveEnterTimestamp` → mark NEEDS_RESTART. Replaced broken token-string comparison.

**Why:** Token-string comparison never detects staleness because the cron refresh script updates both `credentials.json` AND `auth-profiles.json` simultaneously — they're always in sync. The mtime check detects when Claude Code's auto-refresh (or /login) updated credentials without restarting services.

**Files:** `/home/builder/scripts/openclaw-healthcheck.sh`

**Impact on Builder:** After any `/login` or Claude Code auto-token-refresh, Builder is automatically restarted within 5 minutes. No manual intervention needed.

---

## 2026-03-02 Claude Code — Healthcheck Friday memory benchmark cron

**What:** Added a Friday 09:00 UTC trigger in the healthcheck script that runs `/home/builder/scripts/memory_benchmark.py --compare` when the script exists. Marker file prevents re-runs within the same Friday.

**Why:** To send weekly Telegram comparison reports on memory system effectiveness (before/after enabling memory for Builder).

**Files:** `/home/builder/scripts/openclaw-healthcheck.sh` (section 4)

**Status:** Trigger is live. **`memory_benchmark.py` does not exist yet** — Builder needs to create it. The script should: compare memory-assisted vs baseline response quality, then send a Telegram message with results.

**Impact on Builder:** Once you create `memory_benchmark.py`, you will automatically receive Telegram results every Friday at 09:00 UTC.

---

## 2026-03-03 Claude Code — Token usage tracking per agent

**What:** Created `/home/builder/scripts/usage_tracker.py`. Pattern: daily snapshot of cumulative `totalTokens` per agent from sessions.json → delta calculation for any time window → cost estimate for Anthropic agents. Integrated into healthcheck: daily snapshot (deduplicated by date marker), weekly Telegram report every Friday 09:00 UTC.

**Why:** No built-in token tracking in OpenClaw. sessions.json has cumulative totals per session; snapshot-delta gives daily/weekly view. Anthropic cost estimated from input/output/cache tokens using published pricing.

**Files:**
- `/home/builder/scripts/usage_tracker.py` — tracking script
- `/home/builder/scripts/openclaw-healthcheck.sh` — daily snapshot + Friday Telegram report hooks
- `/home/builder/logs/usage-snapshots.json` — snapshot storage (auto-created)

**Usage:**
```bash
python3 /home/builder/scripts/usage_tracker.py --snapshot       # save today
python3 /home/builder/scripts/usage_tracker.py --report         # last 7 days
python3 /home/builder/scripts/usage_tracker.py --report --days 1  # today only
python3 /home/builder/scripts/usage_tracker.py --telegram       # send to Telegram
```

**Impact on Builder:** You'll receive weekly token usage + cost reports on Fridays. Can also ask Claude Code to run `--report` anytime for a current view.

---

## 2026-03-03 Claude Code — Added retry logic to OAuth refresh script

**What:** Added retry with exponential backoff to `oauth_refresh()` in the refresh script. Retries up to 3 times (after 10s, 30s, 60s) on transient failures (5xx, timeout, network errors). Fails immediately on 400 (invalid refresh_token — retry won't help).

**Why:** Anthropic's OAuth API had a ~10-hour outage of 503 errors and timeouts on 2026-03-03. The cron had no retry, so every 2h attempt failed silently and fell back to the cached token. Eventually the token expired. With retry: a single 503 won't cause the cron to give up — it will wait and retry up to 3 times over ~100 seconds before falling back.

**Files:** `/home/builder/scripts/refresh_anthropic_token.py` — `oauth_refresh()` function

**Impact on Builder:** Token refresh is now more resilient to Anthropic API blips. If the API is down for >100 seconds per cron cycle, you'll still get the expired-token Telegram alert. That requires /login to fix.

---

## 2026-03-03 Claude Code — Fixed healthcheck infinite restart loop

**What:** Removed the `expiring_soon` proactive OAuth trigger from the healthcheck. Added `--distribute-only` mode to the refresh script. Healthcheck now NEVER does OAuth refresh — it only distributes credentials.json token to auth-profiles. Added explicit Telegram alert when credentials.json is expired (rather than silently looping).

**Why:** Root cause of the 06:43 loop: the healthcheck's "proactive refresh when <45 min" and the root cron both called `oauth_refresh()` with the same rotating refresh_token. When they raced, one got HTTP 400, fell back to the cached token, and distributed an already-expiring token. Once the token expired the loop became infinite (400 → fallback gives expired token → 401 loop). The fix: healthcheck never does OAuth. The cron handles OAuth every 2h. If the token expires (cron failed), the healthcheck alerts instead of looping.

**Files:**
- `/home/builder/scripts/openclaw-healthcheck.sh` — removed `expiring_soon` trigger, use `--distribute-only`, added `token_expired` alert with exit 0
- `/home/builder/scripts/refresh_anthropic_token.py` — added `--distribute-only` mode (distribute_only function)

**Impact on Builder:** No more restart spam when OAuth is broken. If token expires and cron can't refresh it, you'll get a Telegram alert: "⚠️ Builder: Anthropic token expired and cannot be auto-refreshed. Run /login in Claude Code to restore service." That means Eduard needs to run /login.

---

## 2026-03-02 Claude Code — Created CLAUDE_CONTEXT_LOG.md + SOUL.md update

**What:** Created this shared context log at `/home/builder/workspace/CLAUDE_CONTEXT_LOG.md`. Updated Builder's `SOUL.md` with instructions to check this log at session start and write entries for server-side changes.

**Why:** Two actors (Claude Code + Builder) working on the same server without shared context → blind spots. Builder didn't know about crons Claude Code created; Claude Code didn't know what Builder had changed.

**Files:**
- `/home/builder/workspace/CLAUDE_CONTEXT_LOG.md` (this file, created)
- `/home/builder/workspace/SOUL.md` (updated with shared context section)

**Impact on Builder:** Check this file at session start via `memory_search "CLAUDE_CONTEXT_LOG"` or read it directly. Write entries here when making server-side changes.

## 2026-03-05 Builder — Fixed chuday.eu root path 404 error

**What:** Updated Caddy reverse proxy configuration to redirect root path `/` to `/clawagent/` with permanent redirect (HTTP 301).

**Why:** Lina reported web_fetch failure from https://chuday.eu/. Root cause: OpenClaw gateway only serves content under `/clawagent/*` path, but Caddy was proxying all requests including root `/` which returned 404. 

**Files:** `/home/builder/proxy/Caddyfile`

**Impact on Builder/Lina/Aivar:** Domain now works correctly:
- https://chuday.eu/ → 301 redirect → /clawagent/
- https://chuday.eu/clawagent/ → OpenClaw Control UI (HTTP 200)
- Lina's web_fetch now succeeds

**Related:** Odoo deployment at /home/builder/odoo-deployment/ (created today by Claude Code or Lina, not yet documented in context log).

## 2026-03-05 [Unknown Agent] via Subagent — Odoo v19 deployment for Preservability

**What:** Deployed Odoo Community v19 with Docker Compose at `/home/builder/odoo-deployment/`. Set up company (Preservability), admin user (eduard.chudaikin@gmail.com), Lina PM user, installed CRM + Project modules, created test project with 2 tasks.

**Why:** [Unknown - not documented at time of deployment]

**Files:**
- `/home/builder/odoo-deployment/docker-compose.yml` - PostgreSQL + Odoo services
- `/home/builder/odoo-deployment/setup_odoo_final.py` - Database initialization script
- `/home/builder/odoo-deployment/README.md` - Full deployment documentation
- `/home/builder/odoo-deployment/verify_workflow.py` - Testing script
- `/home/builder/odoo-deployment/simple_setup.py`, `setup_odoo.py` - Alternative setup scripts

**Subagent:** [Unknown - discovered after completion]

**Impact on Builder:** 
- New Docker services running: `odoo_app` (port 8069), `odoo_db` (PostgreSQL)
- Docker volumes: `odoo-db-data`, `odoo-web-data`
- Access URL: http://localhost:8069
- Database name: preservability
- Credentials: eduard.chudaikin@gmail.com/admin (admin), lina@preservability.local/lina123 (PM user)
- **Status:** Services running, not tracked in git

**Note:** This entry was retroactively documented by Builder after discovering the deployment. Going forward, agents must document subagent work immediately per `SUBAGENT_PROTOCOL.md`.

## 2026-03-05 Builder — Switched agents from Codex to Claude due to OpenAI backend errors

**What:** Changed primary model for Lina and Aivar from `openai-codex/gpt-5.3-codex` to `anthropic/claude-sonnet-4-5`. Kept Codex as fallback.

**Why:** OpenAI Codex backend experiencing server errors (request IDs: 3998bf60-9c34-43d5-93fd-96f4f5b7e961, e22b9517-1b44-4743-908a-dea7404ced10, 0675b1da-9f68-4bcd-b4d4-4a4eb90dc393). Lina was failing with "server_error" messages. Preventive switch for Aivar to avoid similar issues.

**Files:**
- `/home/builder/generated_agents/lina-pm-agent/config/openclaw.json`
- `/home/builder/generated_agents/scheduler/config/openclaw.json`

**Impact on Builder:** No impact. Lina and Aivar will use Claude as primary, Codex as fallback. Services await restart (healthcheck will apply within 5 min).
