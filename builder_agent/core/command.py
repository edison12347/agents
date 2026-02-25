from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    code: int
    stdout: str
    stderr: str


class CommandRunner:
    def run(self, args: list[str], cwd: str | None = None) -> CommandResult:
        proc = subprocess.run(
            args,
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
        )
        return CommandResult(code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
