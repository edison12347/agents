from __future__ import annotations

from dataclasses import dataclass

from builder_agent.core.command import CommandRunner
from builder_agent.core.exceptions import AuthError


@dataclass
class ExecutionResult:
    code: int
    stdout: str
    stderr: str


class ExecutionAdapter:
    name: str
    version_cmd: list[str]
    auth_check_cmd: list[str]

    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def validate_authenticated(self) -> None:
        version = self.runner.run(self.version_cmd)
        if version.code != 0:
            raise AuthError(f"{self.name} CLI missing. Install and sign in first.")

        auth = self.runner.run(self.auth_check_cmd)
        if auth.code != 0:
            rendered = " ".join(self.auth_check_cmd)
            raise AuthError(
                f"{self.name} CLI is not authenticated. Run `{rendered}` and complete CLI sign-in."
            )

    def execute(self, prompt: str) -> ExecutionResult:
        raise NotImplementedError
