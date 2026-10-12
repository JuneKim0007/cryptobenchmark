"""Claude Code's headless mode (`claude -p`) as an agent: one CLI session per conversation, continued with
--resume, under the user's existing Claude Code login (no API key).

Context isolation, each flag measured against the CLI: no user or project settings or CLAUDE.md
(--setting-sources ""), no MCP servers (--strict-mcp-config with an empty config: their tool definitions
were 25K tokens), no tools, no skills, no dynamic system-prompt sections, and an empty working directory.
What remains is the CLI's own short preamble and the account's attribution line.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from .reply import AgentRefused, AgentReply

Runner = Callable[[list[str], str, Path], subprocess.CompletedProcess]


class ClaudeCodeError(RuntimeError):
    """The CLI failed for a reason that is not a refusal (not logged in, overloaded, budget)."""


def _run(command: list[str], stdin: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(command, input=stdin, capture_output=True, text=True, cwd=cwd)


class ClaudeCodeSession:

    def __init__(self, owner: "ClaudeCodeConversations", system: str, schema: dict):
        self.owner, self.system, self.schema, self.session_id = owner, system, schema, None

    def ask(self, user: str) -> AgentReply:
        o = self.owner
        command = [o.binary, "-p", "--output-format", "json", "--model", o.model, "--effort", o.effort,
                   "--system-prompt", self.system, "--json-schema", json.dumps(self.schema),
                   "--setting-sources", "", "--strict-mcp-config", "--mcp-config", str(o.no_mcp),
                   "--disable-slash-commands", "--exclude-dynamic-system-prompt-sections", "--tools", ""]
        if self.session_id:
            command += ["--resume", self.session_id]
        # The prompt goes on stdin: --tools takes a variable number of values and would swallow it.
        done = o.runner(command, user, o.workdir)
        try:
            out = json.loads(done.stdout)
        except json.JSONDecodeError:
            raise ClaudeCodeError(f"claude -p exited {done.returncode}: {(done.stderr or done.stdout).strip()[:300]}")
        if out.get("stop_reason") == "refusal":
            raise AgentRefused(str(out.get("result") or "refused"))
        if out.get("is_error") or out.get("subtype") != "success":
            raise ClaudeCodeError(f"claude -p: {out.get('subtype')}: {str(out.get('result'))[:300]}")
        self.session_id = out["session_id"]
        structured = out.get("structured_output")
        text = json.dumps(structured) if structured is not None else str(out.get("result") or "")
        u = out.get("usage") or {}
        return AgentReply(text, o.model, self.session_id, {
            "input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0),
            "cacheRead": u.get("cache_read_input_tokens", 0), "cacheWrite": u.get("cache_creation_input_tokens", 0),
            "costUsd": out.get("total_cost_usd", 0.0)})


class ClaudeCodeConversations:

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium", binary: str = "claude",
                 runner: Runner = _run, workdir: Path | None = None):
        self.model, self.effort, self.binary, self.runner = model, effort, binary, runner
        self.workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="perfrepair-agent-"))
        self.no_mcp = self.workdir / ".no-mcp.json"
        self.no_mcp.write_text(json.dumps({"mcpServers": {}}))

    def start(self, system: str, schema: dict) -> ClaudeCodeSession:
        return ClaudeCodeSession(self, system, schema)


class ClaudeCodeAgent:
    """Agent: one single-turn CLI session per call."""

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium", **kwargs):
        self.conversations = ClaudeCodeConversations(model, effort, **kwargs)

    def __call__(self, system: str, user: str, schema: dict) -> AgentReply:
        return self.conversations.start(system, schema).ask(user)
