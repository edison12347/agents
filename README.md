# Builder (OpenClaw Agent Implementation)

Builder is a concrete, production-oriented implementation of an OpenClaw agent that builds and upgrades other OpenClaw agents.

It is not a standalone agent framework. Builder runs as an OpenClaw agent and uses OpenClaw lifecycle/orchestration primitives.

## What Builder Implements

- OpenClaw-native agent workspace and skill definitions
- Runtime-switchable execution backend:
  - Codex CLI
  - Claude Code CLI
- Doppler-only secret access (no local secret files)
- GitHub release workflow after stable build/upgrade:
  - Conventional commit message format
  - Semver bump + git tag + push
- Agent generation from structured specs
- Optional skills installation from SkillsMP API
- Hetzner Ubuntu deployment via systemd (no Docker)

## Architecture

Builder keeps strict boundaries:

- `builder_agent.adapters.execution`: backend abstraction for Codex/Claude CLIs
- `builder_agent.adapters.secrets`: Doppler integration only
- `builder_agent.adapters.git`: git/github operations + semver
- `builder_agent.adapters.skills`: SkillsMP install/registry sync
- `builder_agent.services`: agent generation, upgrades, workflow logic
- `builder_agent.orchestration`: deterministic sequential lifecycle runner

All orchestration is deterministic and sequential, and intended to be triggered from OpenClaw skill/tool execution.

## Repository Layout

- `config/openclaw.json`: OpenClaw runtime config
- `workspace/`: Builder agent behavior and policy files
- `skills/builder/SKILL.md`: skill entrypoint and workflow
- `builder_agent/`: implementation modules
- `scripts/run_builder.py`: OpenClaw-triggerable runner
- `deploy/systemd/`: native service units
- `generated_agents/`: default output directory for generated agents

## Prerequisites (Hetzner Ubuntu)

- Ubuntu 22.04+ VPS
- Python 3.11+
- `openclaw` CLI installed
- `doppler` CLI installed and authenticated
- At least one backend CLI installed and authenticated:
  - `codex`
  - `claude`
- `git` configured for push access to GitHub

## Quick Start

```bash
cd /home/builder
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp builder.example.yaml builder.yaml
```

Edit `builder.yaml` and set:
- target GitHub repository URL
- backend preference (`codex` or `claude`)
- Doppler project/config

Then run:

```bash
python scripts/run_builder.py --action validate-runtime
python scripts/run_builder.py --action generate --spec examples/new-agent.yaml
```

## Doppler Policy

Builder reads runtime configuration and credentials from Doppler. If required variables are missing, Builder creates placeholders and prints exact population instructions.

No API key auth paths are provided for Codex/Claude. CLI sign-in is required.

## Git Release Policy

- Default branch: `main`
- Working branch for upgrades: `builder/upgrade/<topic>`
- Commit format:
  - `feat(builder): <summary>`
  - `fix(builder): <summary>`
  - `chore(release): vX.Y.Z`
- Version bump rules:
  - `patch`: fixes/internal upgrades
  - `minor`: new capabilities (backward-compatible)
  - `major`: breaking behavior

## OpenClaw Service (systemd)

Use `deploy/systemd/openclaw-builder.service` for native VPS operation.

## Tests

```bash
pytest -q
```
