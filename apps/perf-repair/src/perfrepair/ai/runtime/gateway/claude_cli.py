from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from ....child.deadline import Deadline
from ....child.env import child_env
from ....dto.prompt import CorrectionPrompt, SystemPrompt, TaskPrompt
from ..agent.conversation import LifetimeGuarded
from ..agent.reply import AgentFailed, AgentRefused, AgentReply
from .claude_api import DEFAULT_MODEL

Runner = Callable[[list[str], str, Path, dict[str, str], "int | None"], subprocess.CompletedProcess]


class ClaudeCliError(AgentFailed):
    """Not found, not logged in, overloaded, budget."""

    def __init__(self, detail: str):
        super().__init__("claude_cli_failed", detail)


def _run(command: list[str], stdin: str, cwd: Path, env: dict[str, str], timeout: int | None) -> subprocess.CompletedProcess:
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                          cwd=cwd, env=env, start_new_session=True) as process, Deadline(process, timeout) as deadline:
        out, err = process.communicate(stdin)
    if deadline.expired:
        raise subprocess.TimeoutExpired(command, timeout)
    return subprocess.CompletedProcess(command, process.returncode, out, err)


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
            return o.runner(command, text, o.workdir, child_env(), o.timeout)
        except subprocess.TimeoutExpired:
            raise AgentFailed("claude_cli_timeout", f"{o.binary} -p ran past {o.timeout}s (timeouts.claude); killed") from None
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
                 runner: Runner = _run, workdir: Path | None = None, timeout: int | None = None):
        self.model, self.effort, self.binary, self.runner, self.timeout = model, effort, binary, runner, timeout
        self.workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="perfrepair-agent-"))
        self.no_mcp = self.workdir / ".no-mcp.json"
        self.no_mcp.write_text(json.dumps({"mcpServers": {}}))

    def start(self, system: SystemPrompt, schema: dict) -> ClaudeCliSession:
        return ClaudeCliSession(self, system, schema)
