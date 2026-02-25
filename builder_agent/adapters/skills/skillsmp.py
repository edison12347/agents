from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import requests

from builder_agent.core.command import CommandRunner


@dataclass(frozen=True)
class InstalledSkill:
    skill_id: str
    version: str
    source: str


class SkillsMpClient:
    def __init__(self, base_url: str = "https://skillsmp.com/docs/api") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_metadata(self, skill_id: str) -> dict:
        # Assumes API endpoint contract is hosted under /v1.
        url = f"{self.base_url}/v1/skills/{skill_id}"
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()


class SkillsInstaller:
    def __init__(self, runner: CommandRunner, registry_file: Path, skills_dir: Path) -> None:
        self.runner = runner
        self.registry_file = registry_file
        self.skills_dir = skills_dir

    def _read_registry(self) -> dict[str, dict]:
        if not self.registry_file.exists():
            return {}
        return json.loads(self.registry_file.read_text())

    def _write_registry(self, data: dict[str, dict]) -> None:
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.registry_file.write_text(json.dumps(data, indent=2))

    def install_lazy(self, skill_id: str, metadata: dict) -> InstalledSkill:
        installed = self._read_registry()
        if skill_id in installed:
            current = installed[skill_id]
            return InstalledSkill(
                skill_id=skill_id,
                version=current["version"],
                source=current["source"],
            )

        source = metadata.get("source", "")
        version = metadata.get("version", "0.0.0")
        if source.startswith("http"):
            self.runner.run(["git", "clone", source, str(self.skills_dir / skill_id)])

        installed[skill_id] = {
            "version": version,
            "source": source,
            "compatibility": metadata.get("compatibility", "openclaw"),
        }
        self._write_registry(installed)
        return InstalledSkill(skill_id=skill_id, version=version, source=source)
