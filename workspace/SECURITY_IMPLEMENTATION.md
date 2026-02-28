# Security Model Implementation Summary

**Date:** 2026-02-28  
**Commit:** a5078f6

## Security Policy Implemented

**Agents: Zero Doppler Access**
- Agents cannot run `doppler secrets` or any Doppler CLI commands
- Agents receive credentials only through OpenClaw environment injection
- Agent workspaces include `.agent-env` that blocks doppler access

**Builder: Full Infrastructure Access**
- Builder manages all secrets via Doppler
- Builder updates OpenClaw config with `${VAR}` references
- Builder handles secret provisioning and rotation

**Owner: Control Through Delegation**
- Agents escalate credential needs to Builder
- Builder implements infrastructure changes
- Owner approves through direct Builder communication

## Files Created/Modified

### Documentation
- ✅ `workspace/SECURITY.md` - Complete security model documentation
- ✅ `workspace/AGENTS.md` - Updated with security constraints
- ✅ `generated_agents/scheduler/workspace/TOOLS.md` - Added security section
- ✅ `generated_agents/lina-pm-agent/workspace/TOOLS.md` - Added security section

### Technical Restrictions
- ✅ `generated_agents/scheduler/workspace/.agent-env` - Doppler access blocker
- ✅ `generated_agents/lina-pm-agent/workspace/.agent-env` - Doppler access blocker

## How It Works

**Secret Flow:**
1. Builder adds secret to Doppler: `doppler secrets set API_KEY=xxx`
2. Builder updates OpenClaw config: `"apiKey": "${API_KEY}"`
3. Gateway restart: `doppler run -- openclaw gateway ...`
4. Agent automatically receives secret via environment

**Agent Escalation Pattern:**
```
Agent → Owner: "I need Stripe API access for webhooks"
Owner → Builder: "Add Stripe credentials for [agent]"
Builder: Adds to Doppler + updates config + restarts gateway
Agent: Automatically has credentials on next run
```

## Benefits

- **Security:** Agents can't leak or misuse infrastructure secrets
- **Simplicity:** Agents never manage credentials directly
- **Auditability:** All secret changes flow through Builder with git history
- **Separation of Concerns:** Agents focus on domain logic, Builder handles plumbing

## Future Agent Creation

When creating new agents, Builder will:
1. Create agent workspace without Doppler access
2. Add `.agent-env` to block doppler CLI
3. Document required secrets in agent README
4. Configure secrets in Doppler with `${VAR}` references
5. Test agent receives secrets via environment injection

This pattern is now the standard for all OpenClaw agents in this deployment.
