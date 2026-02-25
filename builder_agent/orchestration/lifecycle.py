from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from builder_agent.adapters.skills.skillsmp import SkillsInstaller, SkillsMpClient
from builder_agent.core.models import BuilderConfig
from builder_agent.services.generator import AgentGenerator
from builder_agent.services.release import ReleaseManager
from builder_agent.services.spec_loader import load_spec
from builder_agent.services.upgrade import AgentUpgrader

logger = logging.getLogger(__name__)


@dataclass
class LifecycleResult:
    action: str
    path: Path | None
    version: str | None


class BuilderLifecycle:
    def __init__(
        self,
        cfg: BuilderConfig,
        generator: AgentGenerator,
        upgrader: AgentUpgrader,
        release_manager: ReleaseManager,
        skills_client: SkillsMpClient,
        skills_installer: SkillsInstaller,
    ) -> None:
        self.cfg = cfg
        self.generator = generator
        self.upgrader = upgrader
        self.release_manager = release_manager
        self.skills_client = skills_client
        self.skills_installer = skills_installer

    def generate(self, spec_path: Path, do_release: bool = True) -> LifecycleResult:
        spec = load_spec(spec_path)
        logger.info("lifecycle.generate.start name=%s", spec.name)
        root = self.generator.generate(spec)
        version = None
        if do_release and self.cfg.release.auto_push:
            version = self.release_manager.release("minor", f"generated {spec.name}")
        logger.info("lifecycle.generate.done name=%s", spec.name)
        return LifecycleResult(action="generate", path=root, version=version)

    def upgrade(self, spec_path: Path, do_release: bool = True) -> LifecycleResult:
        spec = load_spec(spec_path)
        root = self.cfg.paths.generated_agents_dir / spec.name
        logger.info("lifecycle.upgrade.start name=%s", spec.name)
        self.upgrader.upgrade(root, spec)
        version = None
        if do_release and self.cfg.release.auto_push:
            version = self.release_manager.release("patch", f"upgraded {spec.name}")
        logger.info("lifecycle.upgrade.done name=%s", spec.name)
        return LifecycleResult(action="upgrade", path=root, version=version)

    def install_skill(self, skill_id: str) -> LifecycleResult:
        metadata = self.skills_client.fetch_metadata(skill_id)
        compat = metadata.get("compatibility", "openclaw")
        if "openclaw" not in str(compat).lower():
            raise ValueError(f"skill {skill_id} incompatible with OpenClaw: {compat}")
        installed = self.skills_installer.install_lazy(skill_id, metadata)
        logger.info("skill.installed id=%s version=%s", installed.skill_id, installed.version)
        return LifecycleResult(action="install-skill", path=None, version=installed.version)
