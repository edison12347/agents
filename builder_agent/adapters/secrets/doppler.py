from __future__ import annotations

import json
from dataclasses import dataclass

from builder_agent.core.command import CommandRunner
from builder_agent.core.exceptions import SecretError


@dataclass(frozen=True)
class MissingSecretInstruction:
    key: str
    expected_format: str
    command: str


class DopplerSecrets:
    def __init__(self, runner: CommandRunner, project: str, config: str) -> None:
        self.runner = runner
        self.project = project
        self.config = config

    def ensure_cli_ready(self) -> None:
        check = self.runner.run(["doppler", "--version"])
        if check.code != 0:
            raise SecretError("Doppler CLI not installed.")

        auth = self.runner.run(["doppler", "me"])
        if auth.code != 0:
            raise SecretError("Doppler CLI not authenticated. Run `doppler login`.")

    def load_all(self) -> dict[str, str]:
        cmd = [
            "doppler",
            "secrets",
            "download",
            "--no-file",
            "--format",
            "json",
            "--project",
            self.project,
            "--config",
            self.config,
        ]
        res = self.runner.run(cmd)
        if res.code != 0:
            raise SecretError(f"Failed to load Doppler secrets: {res.stderr.strip()}")
        return json.loads(res.stdout)

    def ensure_keys(self, required: dict[str, str]) -> list[MissingSecretInstruction]:
        current = self.load_all()
        missing: list[MissingSecretInstruction] = []
        for key, expected in required.items():
            if current.get(key):
                continue
            placeholder = "REQUIRED_SET_IN_DOPPLER"
            set_cmd = [
                "doppler",
                "secrets",
                "set",
                key,
                placeholder,
                "--project",
                self.project,
                "--config",
                self.config,
            ]
            self.runner.run(set_cmd)
            missing.append(
                MissingSecretInstruction(
                    key=key,
                    expected_format=expected,
                    command=(
                        f"doppler secrets set {key}=<value> --project {self.project} --config {self.config}"
                    ),
                )
            )
        return missing
