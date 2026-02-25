from __future__ import annotations

import logging

from builder_agent.adapters.execution.base import ExecutionAdapter
from builder_agent.adapters.secrets.doppler import DopplerSecrets

logger = logging.getLogger(__name__)


class RuntimeValidator:
    def __init__(self, execution: ExecutionAdapter, doppler: DopplerSecrets) -> None:
        self.execution = execution
        self.doppler = doppler

    def run(self) -> list[str]:
        logger.info("validating backend auth")
        self.execution.validate_authenticated()

        logger.info("validating doppler auth")
        self.doppler.ensure_cli_ready()

        missing = self.doppler.ensure_keys(
            {
                "GITHUB_REPOSITORY_URL": "git@github.com:<org>/<repo>.git",
                "GITHUB_MAIN_BRANCH": "main",
            }
        )
        lines: list[str] = []
        for item in missing:
            lines.append(
                f"missing={item.key} expected={item.expected_format} set_with='{item.command}'"
            )
        return lines
