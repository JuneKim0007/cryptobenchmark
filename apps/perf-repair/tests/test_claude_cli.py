import json
import subprocess

import pytest
from helpers import task

from perfrepair.dto.prompt import CorrectionPrompt, SystemPrompt
from perfrepair.ai.runtime.agent import AgentFailed, AgentRefused
from perfrepair.ai.runtime.gateway.claude_cli import ClaudeCliConversations, ClaudeCliError


class FakeCli:
    def __init__(self, outputs):
        self.outputs, self.calls = list(outputs), []

    def __call__(self, command, stdin, cwd, env, timeout):
        self.calls.append((command, stdin, cwd, env))
        out = self.outputs.pop(0)
        return subprocess.CompletedProcess(command, 0, out if isinstance(out, str) else json.dumps(out), "")


def ok(session, structured):
    return {"type": "result", "subtype": "success", "is_error": False, "stop_reason": "end_turn", "session_id": session,
            "result": json.dumps(structured), "structured_output": structured, "total_cost_usd": 0.01,
            "usage": {"input_tokens": 2, "output_tokens": 9, "cache_read_input_tokens": 800, "cache_creation_input_tokens": 0}}


def test_a_conversation_is_one_isolated_session_resumed_turn_by_turn(tmp_path):
    cli = FakeCli([ok("s-1", {"a": 1}), ok("s-1", {"a": 2})])
    convo = ClaudeCliConversations(runner=cli, workdir=tmp_path).start(SystemPrompt("t", "SYS"), {"type": "object"})
    assert json.loads(convo.ask(task("first")).text) == {"a": 1}
    assert convo.ask(CorrectionPrompt("t", "second")).usage["costUsd"] == 0.01
    first, second = cli.calls[0][0], cli.calls[1][0]
    for flag in ("--setting-sources", "--strict-mcp-config", "--disable-slash-commands", "--tools"):
        assert flag in first
    assert first[first.index("--setting-sources") + 1] == ""
    assert "--resume" not in first and second[second.index("--resume") + 1] == "s-1"
    assert [c[1] for c in cli.calls] == ["first", "second"] and cli.calls[0][2] == tmp_path
    assert json.loads((tmp_path / ".no-mcp.json").read_text()) == {"mcpServers": {}}


def test_a_new_conversation_never_resumes_another(tmp_path):
    cli = FakeCli([ok("s-1", {}), ok("s-2", {})])
    convos = ClaudeCliConversations(runner=cli, workdir=tmp_path)
    convos.start(SystemPrompt("t", "SYS"), {}).ask(task("x"))
    convos.start(SystemPrompt("t", "SYS"), {}).ask(task("y"))
    assert all("--resume" not in c[0] for c in cli.calls)


def test_refusal_and_cli_errors_are_told_apart(tmp_path):
    refused = {**ok("s", {}), "stop_reason": "refusal", "result": "declined"}
    cli = FakeCli([refused, "not json", {**ok("s", {}), "is_error": True, "subtype": "error_max_budget_usd"}])
    convos = ClaudeCliConversations(runner=cli, workdir=tmp_path)
    with pytest.raises(AgentRefused):
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))
    with pytest.raises(ClaudeCliError, match="exited"):
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))
    with pytest.raises(ClaudeCliError, match="error_max_budget_usd"):
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))


def test_system_text_is_a_flag_and_the_message_goes_on_stdin(tmp_path):
    cli = FakeCli([ok("s-1", {})])
    ClaudeCliConversations(runner=cli, workdir=tmp_path).start(SystemPrompt("t", "SYS"), {}).ask(task("MSG"))
    command, stdin, _, _ = cli.calls[0]
    assert command[command.index("--system-prompt") + 1] == "SYS" and stdin == "MSG"


def test_lifetime_misuse_never_reaches_the_cli(tmp_path):
    cli = FakeCli([])
    convo = ClaudeCliConversations(runner=cli, workdir=tmp_path).start(SystemPrompt("t", "S"), {})
    with pytest.raises(TypeError, match="lifetime_mismatch"):
        convo.ask(CorrectionPrompt("t", "x"))
    assert cli.calls == []


def test_the_child_never_sees_the_credentials_and_runs_the_configured_binary(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "token-test")
    monkeypatch.setenv("KEEP_ME", "1")
    cli = FakeCli([ok("s-1", {})])
    convos = ClaudeCliConversations(binary="/opt/claude", runner=cli, workdir=tmp_path)
    convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))
    command, _, _, env = cli.calls[0]
    assert command[0] == "/opt/claude" and env["KEEP_ME"] == "1"
    assert "ANTHROPIC_API_KEY" not in env and "ANTHROPIC_AUTH_TOKEN" not in env


def test_a_limit_notice_is_a_failure_never_an_answer_to_reject(tmp_path):
    notice = {**ok("s", {}), "structured_output": None, "result": "usage limit reached",
              "usage": {"input_tokens": 0, "output_tokens": 0}}
    convos = ClaudeCliConversations(runner=FakeCli([notice]), workdir=tmp_path)
    with pytest.raises(ClaudeCliError, match="no model output: usage limit reached"):
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))


def test_a_nonzero_exit_with_json_on_stdout_is_a_failure(tmp_path):
    runner = lambda c, *_: subprocess.CompletedProcess(c, 1, json.dumps(ok("s", {})), "")  # noqa: E731
    convos = ClaudeCliConversations(runner=runner, workdir=tmp_path)
    with pytest.raises(ClaudeCliError):
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))


def test_a_multi_line_cli_failure_is_one_coded_line(tmp_path):
    convos = ClaudeCliConversations(runner=lambda c, *_: subprocess.CompletedProcess(c, 1, "", "line one\nline two\n"),
                                    workdir=tmp_path)
    with pytest.raises(ClaudeCliError) as e:
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))
    assert str(e.value) == "claude_cli_failed: claude -p exited 1: line one line two"


def test_a_cli_failing_with_no_output_says_so(tmp_path):
    convos = ClaudeCliConversations(runner=lambda c, *_: subprocess.CompletedProcess(c, 1, "", ""), workdir=tmp_path)
    with pytest.raises(ClaudeCliError, match="claude -p exited 1: no output"):
        convos.start(SystemPrompt("t", "S"), {}).ask(task("MSG"))


def test_a_hung_cli_is_killed_at_its_timeout_as_one_coded_failure(tmp_path):
    hung = tmp_path / "claude"
    hung.write_text("#!/bin/sh\nsleep 60\n")
    hung.chmod(0o755)
    convos = ClaudeCliConversations(binary=str(hung), workdir=tmp_path, timeout=1)
    with pytest.raises(AgentFailed) as e:
        convos.start(SystemPrompt("t", "S"), {}).ask(task("x"))
    assert e.value.code == "claude_cli_timeout" and "ran past 1s (timeouts.claude)" in str(e.value)
