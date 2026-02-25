from __future__ import annotations

from builder_agent.adapters.execution.base import ExecutionAdapter
from builder_agent.adapters.execution.claude_cli import ClaudeCliAdapter
from builder_agent.adapters.execution.codex_cli import CodexCliAdapter
from builder_agent.core.command import CommandRunner


def build_execution_adapter(name: str, runner: CommandRunner) -> ExecutionAdapter:
    normalized = name.strip().lower()
    if normalized == "codex":
        return CodexCliAdapter(runner)
    if normalized == "claude":
        return ClaudeCliAdapter(runner)
    raise ValueError(f"Unsupported backend: {name}")
