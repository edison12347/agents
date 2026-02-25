from __future__ import annotations

from pathlib import Path

import yaml

from builder_agent.core.models import AgentSpec


def load_spec(path: Path) -> AgentSpec:
    raw = yaml.safe_load(path.read_text())
    return AgentSpec(
        name=raw["name"],
        description=raw["description"],
        model_primary=raw.get("model", {}).get("primary", "anthropic/claude-sonnet-4-5"),
        workspace_path=Path(raw.get("workspace_path", f"/home/builder/generated_agents/{raw['name']}/workspace")),
        skills=list(raw.get("skills", [])),
        channels=dict(raw.get("channels", {})),
    )
