#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("OPENCLAW_CONFIG_PATH", "/home/builder/config/openclaw.json"))
STATE_DIR = Path(os.environ.get("OPENCLAW_STATE_DIR", "/root/.openclaw"))


def provider_from_model(model: str) -> str:
    # e.g. anthropic/claude-sonnet-4-5 -> anthropic
    return model.split("/", 1)[0].strip()


def providers_for_agent(agent: dict, defaults: dict) -> set[str]:
    providers: set[str] = set()

    # Model can be string or object in per-agent and defaults
    agent_model = agent.get("model")
    defaults_model = defaults.get("model")

    candidates: list[str] = []

    def collect(model_field):
        if isinstance(model_field, str):
            candidates.append(model_field)
        elif isinstance(model_field, dict):
            primary = model_field.get("primary")
            if isinstance(primary, str):
                candidates.append(primary)
            for fb in model_field.get("fallbacks", []) or []:
                if isinstance(fb, str):
                    candidates.append(fb)

    collect(defaults_model)
    collect(agent_model)

    for model in candidates:
        if "/" in model:
            providers.add(provider_from_model(model))

    return providers


def load_auth_providers(auth_path: Path) -> set[str]:
    raw = json.loads(auth_path.read_text())
    providers: set[str] = set()
    for prof in (raw.get("profiles") or {}).values():
        provider = prof.get("provider")
        if isinstance(provider, str) and provider:
            providers.add(provider)
    return providers


def main() -> int:
    if not CONFIG_PATH.exists():
        print(f"[startup-check] missing config: {CONFIG_PATH}", file=sys.stderr)
        return 1

    cfg = json.loads(CONFIG_PATH.read_text())
    defaults = ((cfg.get("agents") or {}).get("defaults") or {})
    agent_list = ((cfg.get("agents") or {}).get("list") or [])

    if not agent_list:
        print("[startup-check] no agents configured", file=sys.stderr)
        return 1

    failures: list[str] = []
    for agent in agent_list:
        agent_id = agent.get("id")
        if not isinstance(agent_id, str) or not agent_id:
            failures.append("agent entry missing id")
            continue

        required_providers = providers_for_agent(agent, defaults)
        if not required_providers:
            failures.append(f"agent={agent_id}: no model providers resolved from config")
            continue

        auth_path = STATE_DIR / "agents" / agent_id / "agent" / "auth-profiles.json"
        if not auth_path.exists():
            failures.append(f"agent={agent_id}: missing auth store {auth_path}")
            continue

        auth_providers = load_auth_providers(auth_path)
        missing = sorted(p for p in required_providers if p not in auth_providers)
        if missing:
            failures.append(
                f"agent={agent_id}: missing provider auth for {','.join(missing)} in {auth_path}"
            )

    if failures:
        print("[startup-check] FAILED", file=sys.stderr)
        for line in failures:
            print(f" - {line}", file=sys.stderr)
        return 1

    print("[startup-check] OK: provider auth/model checks passed for all configured agents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
