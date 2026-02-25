#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from builder_agent.adapters.execution.factory import build_execution_adapter
from builder_agent.adapters.git.github import GitHubRelease
from builder_agent.adapters.secrets.doppler import DopplerSecrets
from builder_agent.adapters.skills.skillsmp import SkillsInstaller, SkillsMpClient
from builder_agent.core.command import CommandRunner
from builder_agent.core.config import load_config
from builder_agent.core.logging import setup_logging
from builder_agent.orchestration.lifecycle import BuilderLifecycle
from builder_agent.services.generator import AgentGenerator
from builder_agent.services.release import ReleaseManager
from builder_agent.services.runtime_validation import RuntimeValidator
from builder_agent.services.upgrade import AgentUpgrader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Builder OpenClaw agent runner")
    parser.add_argument("--config", default="/home/builder/builder.yaml")
    parser.add_argument("--action", required=True, choices=["validate-runtime", "generate", "upgrade", "install-skill"])
    parser.add_argument("--spec", help="Path to agent specification YAML")
    parser.add_argument("--backend", choices=["codex", "claude"], help="Override configured backend")
    parser.add_argument("--skill-id", help="Skill ID for install-skill action")
    parser.add_argument("--no-release", action="store_true", help="Skip commit/tag/push")
    return parser.parse_args()


def main() -> int:
    setup_logging()
    args = parse_args()
    cfg = load_config(Path(args.config))

    runner = CommandRunner()
    backend_name = args.backend or cfg.backend.name
    execution = build_execution_adapter(backend_name, runner)
    doppler = DopplerSecrets(runner, cfg.doppler.project, cfg.doppler.config)

    if args.action == "validate-runtime":
        validator = RuntimeValidator(execution, doppler)
        missing = validator.run()
        if missing:
            print("Missing required secrets placeholders created:")
            for line in missing:
                print(f"- {line}")
        else:
            print("Runtime validation passed")
        return 0

    git = GitHubRelease(runner, Path("/home/builder"), default_branch=cfg.repo.default_branch)
    git.ensure_remote(cfg.repo.url)

    release = ReleaseManager(git, tag_prefix=cfg.release.tag_prefix)
    lifecycle = BuilderLifecycle(
        cfg=cfg,
        generator=AgentGenerator(cfg),
        upgrader=AgentUpgrader(),
        release_manager=release,
        skills_client=SkillsMpClient(),
        skills_installer=SkillsInstaller(
            runner=runner,
            registry_file=cfg.skills_registry_file,
            skills_dir=Path("/home/builder/skills"),
        ),
    )

    if args.action in {"generate", "upgrade"} and not args.spec:
        raise SystemExit("--spec is required for generate/upgrade")

    if args.action == "generate":
        result = lifecycle.generate(Path(args.spec), do_release=not args.no_release)
        print(f"Generated agent at {result.path}")
        if result.version:
            print(f"Released version {cfg.release.tag_prefix}{result.version}")
        return 0

    if args.action == "upgrade":
        result = lifecycle.upgrade(Path(args.spec), do_release=not args.no_release)
        print(f"Upgraded agent at {result.path}")
        if result.version:
            print(f"Released version {cfg.release.tag_prefix}{result.version}")
        return 0

    if args.action == "install-skill":
        if not args.skill_id:
            raise SystemExit("--skill-id is required for install-skill")
        result = lifecycle.install_skill(args.skill_id)
        print(f"Installed skill {args.skill_id} version {result.version}")
        return 0

    raise SystemExit(f"unsupported action: {args.action}")


if __name__ == "__main__":
    raise SystemExit(main())
