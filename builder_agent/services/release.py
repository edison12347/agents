from __future__ import annotations

from builder_agent.adapters.git.github import GitHubRelease


class ReleaseManager:
    def __init__(self, git: GitHubRelease, tag_prefix: str = "v") -> None:
        self.git = git
        self.tag_prefix = tag_prefix

    def release(self, bump_type: str, summary: str) -> str:
        new_version = self.git.bump(bump_type)
        commit_message = f"chore(release): {self.tag_prefix}{new_version} - {summary}"
        self.git.commit_tag_push(commit_message, new_version, tag_prefix=self.tag_prefix)
        return new_version
