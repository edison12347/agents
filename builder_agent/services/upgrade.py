from __future__ import annotations

from pathlib import Path

from builder_agent.core.models import AgentSpec


class AgentUpgrader:
    def upgrade(self, root: Path, spec: AgentSpec) -> None:
        readme = root / "README.md"
        if readme.exists():
            content = readme.read_text()
            marker = "\n\n## Upgrade Notes\n"
            if marker not in content:
                content += marker
            content += "- Upgraded by Builder using latest structured spec.\n"
            readme.write_text(content)
