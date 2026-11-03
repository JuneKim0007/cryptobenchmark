from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from ....dto.prompt import CorrectionPrompt, SystemPrompt, TaskPrompt
from ..agent.conversation import LifetimeGuarded
from ..agent.reply import AgentFailed, AgentRefused, AgentReply
from .claude_api import DEFAULT_MODEL

Runner = Callable[[list[str], str, Path, dict[str, str]], subprocess.CompletedProcess]
# The CLI bills an API key it finds before the logged-in subscription.
WITHHELD_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


class ClaudeCliError(AgentFailed):
    """Not found, not logged in, overloaded, budget."""

    def __init__(self, detail: str):
        super().__init__("claude_cli_failed", detail)


def _run(command: list[str], stdin: str, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, input=stdin, capture_output=True, text=True, cwd=cwd, env=env)


def child_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in WITHHELD_ENV}


def _raise_unless_answered(returncode: int, out: dict) -> None:
    if returncode != 0 or out.get("is_error") or out.get("subtype") != "success":
        raise ClaudeCliError(f"claude -p: {out.get('subtype')}: {str(out.get('result'))[:300]}")
    # no model wrote this (a limit notice): as an answer it would be rejected until the item is dropped
    if out.get("usage") and not out["usage"].get("output_tokens"):
        raise ClaudeCliError(f"claude -p: no model output: {str(out.get('result'))[:300]}")


class ClaudeCliSession(LifetimeGuarded):

    def __init__(self, owner: "ClaudeCliConversations", system: SystemPrompt, schema: dict):
        super().__init__(system)
        self.owner, self.schema, self.session_id = owner, schema, None

    def _ran(self, command: list[str], text: str) -> subprocess.CompletedProcess:
        o = self.owner
        try:
            return o.runner(command, text, o.workdir, child_env())
        except OSError as e:
            raise ClaudeCliError(f"cannot run {o.binary}: {e}") from e

    def _send(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply:
        o = self.owner
        command = [o.binary, "-p", "--output-format", "json", "--model", o.model, "--effort", o.effort,
                   "--system-prompt", self.system.text, "--json-schema", json.dumps(self.schema),
                   "--setting-sources", "", "--strict-mcp-config", "--mcp-config", str(o.no_mcp),
                   "--disable-slash-commands", "--exclude-dynamic-system-prompt-sections", "--tools", ""]
        if self.session_id:
            command += ["--resume", self.session_id]
        # The prompt goes on stdin: --tools takes a variable number of values and would swallow it.
        done = self._ran(command, message.text)
        try:
            out = json.loads(done.stdout)
        except json.JSONDecodeError:
            raise ClaudeCliError(f"claude -p exited {done.returncode}: {(done.stderr or done.stdout).strip()[:300] or 'no output'}")
        if out.get("stop_reason") == "refusal":
            raise AgentRefused(str(out.get("result") or "refused"))
        _raise_unless_answered(done.returncode, out)
        self.session_id = out["session_id"]
        structured = out.get("structured_output")
        text = json.dumps(structured) if structured is not None else str(out.get("result") or "")
        u = out.get("usage") or {}
        return AgentReply(text, o.model, self.session_id, {
            "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
            "cacheRead": u.get("cache_read_input_tokens", 0), "cacheWrite": u.get("cache_creation_input_tokens", 0),
            "costUsd": out.get("total_cost_usd", 0.0)})


class ClaudeCliConversations:

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium", binary: str = "claude",
                 runner: Runner = _run, workdir: Path | None = None):
        self.model, self.effort, self.binary, self.runner = model, effort, binary, runner
        self.workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="perfrepair-agent-"))
        self.no_mcp = self.workdir / ".no-mcp.json"
        self.no_mcp.write_text(json.dumps({"mcpServers": {}}))

    def start(self, system: SystemPrompt, schema: dict) -> ClaudeCliSession:
        return ClaudeCliSession(self, system, schema)
