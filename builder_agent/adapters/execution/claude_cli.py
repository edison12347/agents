from __future__ import annotations

from builder_agent.adapters.execution.base import ExecutionAdapter, ExecutionResult


class ClaudeCliAdapter(ExecutionAdapter):
    name = "claude"
    version_cmd = ["claude", "--version"]
    auth_check_cmd = ["claude", "auth", "status"]

    def execute(self, prompt: str) -> ExecutionResult:
        res = self.runner.run(["claude", "--print", prompt])
        return ExecutionResult(code=res.code, stdout=res.stdout, stderr=res.stderr)
