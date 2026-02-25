from pathlib import Path

from builder_agent.core.models import (
    BackendConfig,
    BuilderConfig,
    DopplerConfig,
    PathsConfig,
    ReleaseConfig,
    RepoConfig,
    AgentSpec,
)
from builder_agent.services.generator import AgentGenerator


def test_generator_layout(tmp_path: Path):
    cfg = BuilderConfig(
        version=1,
        backend=BackendConfig(name="codex"),
        doppler=DopplerConfig(project="x", config="y"),
        repo=RepoConfig(url="git@github.com:x/y.git", default_branch="main"),
        release=ReleaseConfig(auto_push=False, tag_prefix="v"),
        paths=PathsConfig(generated_agents_dir=tmp_path, logs_dir=tmp_path / "logs"),
        skills_enabled=True,
        skills_registry_file=tmp_path / "reg.json",
    )
    spec = AgentSpec(
        name="demo",
        description="demo agent",
        model_primary="anthropic/claude-sonnet-4-5",
        workspace_path=tmp_path / "demo" / "workspace",
        skills=["builder"],
        channels={},
    )

    root = AgentGenerator(cfg).generate(spec)
    assert (root / "config" / "openclaw.json").exists()
    assert (root / "workspace" / "AGENTS.md").exists()
