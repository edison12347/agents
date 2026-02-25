from __future__ import annotations

import re
from pathlib import Path

from builder_agent.core.command import CommandRunner
from builder_agent.core.exceptions import ReleaseError


SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class GitHubRelease:
    def __init__(self, runner: CommandRunner, repo_dir: Path, default_branch: str = "main") -> None:
        self.runner = runner
        self.repo_dir = str(repo_dir)
        self.default_branch = default_branch

    def ensure_remote(self, url: str) -> None:
        current = self.runner.run(["git", "remote", "get-url", "origin"], cwd=self.repo_dir)
        if current.code == 0:
            return
        add = self.runner.run(["git", "remote", "add", "origin", url], cwd=self.repo_dir)
        if add.code != 0:
            raise ReleaseError(add.stderr.strip())

    def current_version(self) -> str:
        tag = self.runner.run(["git", "describe", "--tags", "--abbrev=0"], cwd=self.repo_dir)
        if tag.code != 0:
            return "0.0.0"
        return tag.stdout.strip().lstrip("v")

    def bump(self, bump_type: str) -> str:
        current = self.current_version()
        m = SEMVER_PATTERN.match(current)
        if not m:
            raise ReleaseError(f"Invalid semver tag: {current}")
        major, minor, patch = map(int, m.groups())

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1
        return f"{major}.{minor}.{patch}"

    def commit_tag_push(self, message: str, new_version: str, tag_prefix: str = "v") -> None:
        add = self.runner.run(["git", "add", "."], cwd=self.repo_dir)
        if add.code != 0:
            raise ReleaseError(add.stderr.strip())

        commit = self.runner.run(["git", "commit", "-m", message], cwd=self.repo_dir)
        if commit.code != 0 and "nothing to commit" not in commit.stderr.lower():
            raise ReleaseError(commit.stderr.strip())

        tag = self.runner.run(["git", "tag", f"{tag_prefix}{new_version}"], cwd=self.repo_dir)
        if tag.code != 0:
            raise ReleaseError(tag.stderr.strip())

        push_branch = self.runner.run(["git", "push", "origin", self.default_branch], cwd=self.repo_dir)
        if push_branch.code != 0:
            raise ReleaseError(push_branch.stderr.strip())

        push_tag = self.runner.run(["git", "push", "origin", f"{tag_prefix}{new_version}"], cwd=self.repo_dir)
        if push_tag.code != 0:
            raise ReleaseError(push_tag.stderr.strip())
