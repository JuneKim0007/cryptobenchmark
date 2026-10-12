import json
import subprocess

import pytest

from perfrepair.orchestrate.agent import AgentRefused, ClaudeCodeConversations, ClaudeCodeError


class FakeCli:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def __call__(self, command, stdin, cwd):
        self.calls.append((command, stdin, cwd))
        out = self.outputs.pop(0)
        return subprocess.CompletedProcess(command, 0, out if isinstance(out, str) else json.dumps(out), "")


def ok(session, structured):
    return {"type": "result", "subtype": "success", "is_error": False, "stop_reason": "end_turn", "session_id": session,
            "result": json.dumps(structured), "structured_output": structured, "total_cost_usd": 0.01,
            "usage": {"input_tokens": 2, "output_tokens": 9, "cache_read_input_tokens": 800, "cache_creation_input_tokens": 0}}


def test_a_conversation_is_one_isolated_session_resumed_turn_by_turn(tmp_path):
    cli = FakeCli([ok("s-1", {"a": 1}), ok("s-1", {"a": 2})])
    convo = ClaudeCodeConversations(runner=cli, workdir=tmp_path).start("SYS", {"type": "object"})
    assert json.loads(convo.ask("first").text) == {"a": 1}
    assert convo.ask("second").usage["costUsd"] == 0.01
    first, second = cli.calls[0][0], cli.calls[1][0]
    for flag in ("--setting-sources", "--strict-mcp-config", "--disable-slash-commands", "--tools"):
        assert flag in first
    assert first[first.index("--setting-sources") + 1] == ""
    assert "--resume" not in first and second[second.index("--resume") + 1] == "s-1"
    assert [c[1] for c in cli.calls] == ["first", "second"] and cli.calls[0][2] == tmp_path
    assert json.loads((tmp_path / ".no-mcp.json").read_text()) == {"mcpServers": {}}


def test_a_new_conversation_never_resumes_another(tmp_path):
    cli = FakeCli([ok("s-1", {}), ok("s-2", {})])
    convos = ClaudeCodeConversations(runner=cli, workdir=tmp_path)
    convos.start("SYS", {}).ask("x")
    convos.start("SYS", {}).ask("y")
    assert all("--resume" not in c[0] for c in cli.calls)


def test_refusal_and_cli_errors_are_told_apart(tmp_path):
    refused = {**ok("s", {}), "stop_reason": "refusal", "result": "declined"}
    cli = FakeCli([refused, "not json", {**ok("s", {}), "is_error": True, "subtype": "error_max_budget_usd"}])
    convos = ClaudeCodeConversations(runner=cli, workdir=tmp_path)
    with pytest.raises(AgentRefused):
        convos.start("S", {}).ask("x")
    with pytest.raises(ClaudeCodeError, match="exited"):
        convos.start("S", {}).ask("x")
    with pytest.raises(ClaudeCodeError, match="error_max_budget_usd"):
        convos.start("S", {}).ask("x")
