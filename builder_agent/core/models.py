from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BackendConfig:
    name: str


@dataclass(frozen=True)
class DopplerConfig:
    project: str
    config: str


@dataclass(frozen=True)
class RepoConfig:
    url: str
    default_branch: str = "main"


@dataclass(frozen=True)
class ReleaseConfig:
    auto_push: bool = True
    tag_prefix: str = "v"


@dataclass(frozen=True)
class PathsConfig:
    generated_agents_dir: Path
    logs_dir: Path


@dataclass(frozen=True)
class BuilderConfig:
    version: int
    backend: BackendConfig
    doppler: DopplerConfig
    repo: RepoConfig
    release: ReleaseConfig
    paths: PathsConfig
    skills_enabled: bool
    skills_registry_file: Path


@dataclass(frozen=True)
class AgentSpec:
    name: str
    description: str
    model_primary: str
    workspace_path: Path
    skills: list[str]
    channels: dict[str, Any]
