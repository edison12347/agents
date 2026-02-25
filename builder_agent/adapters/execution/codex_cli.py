from __future__ import annotations

from builder_agent.adapters.execution.base import ExecutionAdapter, ExecutionResult


class CodexCliAdapter(ExecutionAdapter):
    name = "codex"
    version_cmd = ["codex", "--version"]
    auth_check_cmd = ["codex", "auth", "status"]

    def execute(self, prompt: str) -> ExecutionResult:
        res = self.runner.run(["codex", "exec", prompt])
        return ExecutionResult(code=res.code, stdout=res.stdout, stderr=res.stderr)
