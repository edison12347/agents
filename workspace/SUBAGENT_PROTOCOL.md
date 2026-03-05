# Subagent Completion Protocol

## When Agents Spawn Subagents for Builder Work

If Lina/Aivar spawn a subagent to do Builder's work (infrastructure, deployments, scripts), the **spawning agent must:**

### 1. After Subagent Completes
Add entry to `CLAUDE_CONTEXT_LOG.md`:

```markdown
## [YYYY-MM-DD] [Agent] via Subagent — [Title]
**What:** Brief description of work done
**Why:** Reason for the work
**Files:** List of files created/modified
**Subagent:** [run ID or identifier]
**Impact on Builder:** What Builder needs to know
```

### 2. For Important Infrastructure Changes
Also update `MEMORY.md` if the change is durable (new services, deployments, configs).

### 3. Send Builder Notification
Use `sessions_send` to notify Builder:
```
Hey Builder, I just completed [task] via subagent. Details in CLAUDE_CONTEXT_LOG.md (entry: [date] [title]).
```

## Example

**Lina spawns subagent to deploy Odoo:**

**After completion, Lina writes:**
```markdown
## 2026-03-05 Lina via Subagent — Odoo v19 deployment for Preservability

**What:** Deployed Odoo Community v19 with Docker Compose at `/home/builder/odoo-deployment/`. Set up company (Preservability), admin user (eduard.chudaikin@gmail.com), Lina PM user, installed CRM + Project modules, created test project.

**Why:** Eduard requested Odoo for project/CRM management integration.

**Files:** 
- `/home/builder/odoo-deployment/docker-compose.yml`
- `/home/builder/odoo-deployment/setup_odoo_final.py`
- `/home/builder/odoo-deployment/README.md`

**Subagent:** builder-odoo-setup-20260305

**Impact on Builder:** New Docker services running (odoo_app, odoo_db). Port 8069 occupied. Database: preservability. No action needed unless services need restart.
```

**Then Lina sends:**
```
Builder, I deployed Odoo v19 via subagent. Full details in CLAUDE_CONTEXT_LOG.md (2026-03-05 Odoo deployment entry).
```

## Why This Works

- ✅ Builder checks `CLAUDE_CONTEXT_LOG.md` at session start
- ✅ Memory search picks up subagent work
- ✅ Notification ensures immediate awareness
- ✅ Audit trail for all infrastructure changes
- ✅ No blind spots between sessions

## Agent Responsibilities

**Lina/Aivar (delegating agents):**
- Write context log entry after subagent completes
- Notify Builder if urgent/important
- Update MEMORY.md for durable changes

**Builder:**
- Check `CLAUDE_CONTEXT_LOG.md` at session start
- Use `memory_search` when picking up context
- Write own entries for work done directly

**Subagents:**
- Complete work as requested
- Report back to spawning agent (automatic)
- No direct logging responsibility
