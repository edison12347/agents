from __future__ import annotations

from pathlib import Path

import yaml

from builder_agent.core.models import (
    BackendConfig,
    BuilderConfig,
    DopplerConfig,
    PathsConfig,
    ReleaseConfig,
    RepoConfig,
)


def load_config(path: Path) -> BuilderConfig:
    raw = yaml.safe_load(path.read_text())
    return BuilderConfig(
        version=int(raw.get("version", 1)),
        backend=BackendConfig(name=raw["backend"]),
        doppler=DopplerConfig(
            project=raw["doppler"]["project"],
            config=raw["doppler"]["config"],
        ),
        repo=RepoConfig(
            url=raw["repo"]["url"],
            default_branch=raw["repo"].get("default_branch", "main"),
        ),
        release=ReleaseConfig(
            auto_push=bool(raw["release"].get("auto_push", True)),
            tag_prefix=raw["release"].get("tag_prefix", "v"),
        ),
        paths=PathsConfig(
            generated_agents_dir=Path(raw["paths"]["generated_agents_dir"]),
            logs_dir=Path(raw["paths"]["logs_dir"]),
        ),
        skills_enabled=bool(raw.get("skills", {}).get("enabled", True)),
        skills_registry_file=Path(
            raw.get("skills", {}).get(
                "registry_file", "/home/builder/generated_agents/skills_registry.json"
            )
        ),
    )
