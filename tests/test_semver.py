from pathlib import Path

from builder_agent.adapters.git.github import GitHubRelease


class DummyRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, args, cwd=None):
        self.calls.append((args, cwd))
        if args[:4] == ["git", "describe", "--tags", "--abbrev=0"]:
            class R:
                code = 0
                stdout = "v1.2.3\n"
                stderr = ""
            return R()
        class X:
            code = 0
            stdout = ""
            stderr = ""
        return X()


def test_semver_patch_bump():
    git = GitHubRelease(DummyRunner(), Path("."))
    assert git.bump("patch") == "1.2.4"


def test_semver_minor_bump():
    git = GitHubRelease(DummyRunner(), Path("."))
    assert git.bump("minor") == "1.3.0"


def test_semver_major_bump():
    git = GitHubRelease(DummyRunner(), Path("."))
    assert git.bump("major") == "2.0.0"
