import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from helpers import with_results, SYSTEM, task

from perfrepair.ai.__main__ import main as ai
from perfrepair.ai.runtime.agent import AgentFailed, ScriptedConversations
from perfrepair.ai.runtime.gateway import registry
from perfrepair.ai.runtime.gateway.args import add_agent_args
from perfrepair.ai.runtime.gateway.claude_api import ClaudeConversations
from perfrepair.ai.runtime.gateway.claude_cli import ClaudeCliConversations
from perfrepair.ai.runtime.gateway.contract import Gateway
from perfrepair.ai.runtime.gateway.spawn import spawn
from perfrepair.config import dotenv
from perfrepair.config.args import load_settings
from perfrepair.inputs.check import Invalid, check_one_of
from perfrepair.inputs.table import APPS_AGENT, GROUPING_ASSIGN
from perfrepair.data_handler.inbound.__main__ import main as inbound
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.guide.command import main as guide

DRY = ScriptedConversations(lambda *_: {})
F = Path(__file__).parent / "fixtures" / "results" / "test-api36-00000000" / "manifest.yaml"
EXAMPLE = Path(__file__).parents[1] / "perfrepair.example.yaml"


def spawned(tmp_path, text="", argv=(), role=GROUPING_ASSIGN):
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role=role)
    config = tmp_path / "c.yaml"
    config.write_text(text)
    args = ap.parse_args(["--perfrepair-config", str(config), *argv])
    return spawn(args, load_settings(ap, args), DRY)


def error(tmp_path, text="", argv=(), role=GROUPING_ASSIGN):
    with pytest.raises(ValueError) as e:
        spawned(tmp_path, text, argv, role)
    assert "\n" not in str(e.value)
    return str(e.value)


def test_the_flags_reach_the_gateway_and_the_help_names_the_role_default(tmp_path):
    convos = spawned(tmp_path, argv=["--effort", "high", "--agent", "claude", "--model", "m"])
    assert isinstance(convos.conversations, ClaudeCliConversations) and (convos.conversations.effort, convos.conversations.model) == ("high", "m")


def test_a_role_can_take_its_own_gateway_and_dry_run_answers_are_the_roles(tmp_path):
    text = "aiGateway: {use: claude}\ndevice: {grouping: {assign: {gateway: dry-run}}}\n"
    assert spawned(tmp_path, text).conversations is DRY
    assert isinstance(spawned(tmp_path, text, role=APPS_AGENT).conversations, ClaudeCliConversations)
    assert spawned(tmp_path, text).identity.gateway == "dry-run" and spawned(tmp_path, text).identity.model is None


def test_dotenv_fills_the_gateway_below_the_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("PERFREPAIR_AGENT=dry-run\n")
    monkeypatch.setattr(dotenv, "ENV_FILE", tmp_path / ".env")
    assert spawned(tmp_path).conversations is DRY
    assert isinstance(spawned(tmp_path, "aiGateway: {use: claude}\n").conversations, ClaudeCliConversations)


def test_auth_api_needs_its_secret_before_any_work_and_withholds_nothing_from_its_client(tmp_path, monkeypatch):
    pytest.importorskip("anthropic")
    assert error(tmp_path, "aiGateway: {claude: {auth: api}}\n").startswith("missing_secret: ANTHROPIC_API_KEY")
    assert error(tmp_path, argv=["--auth", "api"]).startswith("missing_secret")
    monkeypatch.setenv("PERFREPAIR_AUTH", "api")
    assert error(tmp_path).startswith("missing_secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    convos = spawned(tmp_path).conversations
    assert isinstance(convos, ClaudeConversations)


def test_a_dotenv_secret_is_enough(tmp_path, monkeypatch):
    pytest.importorskip("anthropic")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=x\n")
    monkeypatch.setattr(dotenv, "ENV_FILE", tmp_path / ".env")
    assert isinstance(spawned(tmp_path, argv=["--auth", "api"]).conversations, ClaudeConversations)


def test_a_missing_sdk_is_one_coded_line(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(AgentFailed, match="^claude_api_missing: "):
        spawned(tmp_path, argv=["--auth", "api"])


@pytest.mark.parametrize("text, environ, prefix", [
    ("aiGateway: {use: gemini}\n", {}, "unknown_gateway: gemini"),
    ("device: {grouping: {assign: {gateway: gemini}}}\n", {}, "unknown_gateway: gemini"),
    ("", {"PERFREPAIR_AGENT": "claude-code"}, "unknown_gateway: claude-code"),
    ("aiGateway: {gemini: {model: m}}\n", {}, "unknown_gateway: gemini"),
    ("aiGateway: {use: dry-run, claude: {auth: oauth}}\n", {}, "invalid: aiGateway.claude.auth"),
    ("aiGateway: {use: 3}\n", {}, "invalid: device.grouping.assign.gateway"),
    ("", {"PERFREPAIR_AUTH": "x"}, "invalid: device.grouping.assign.auth"),
])
def test_every_settings_error_at_spawn_is_one_coded_line(tmp_path, monkeypatch, text, environ, prefix):
    for key, value in environ.items():
        monkeypatch.setenv(key, value)
    assert error(tmp_path, text).startswith(prefix)


@pytest.mark.parametrize("text, environ, prefix, effort", [
    ("aiGateway: {claude: {effrt: low}}\n", {}, "unknown_key: aiGateway.claude.effrt", "low"),
    ("aiGateway: {dry-run: {model: m}}\n", {}, "unknown_key: aiGateway.dry-run.model", "low"),
    ("aiGateway: {use: dry-run, claude: {effort: hgh}}\n", {}, "invalid: aiGateway.claude.effort", None),
    ("aiGateway: {claude: {binary: 3}}\n", {}, "invalid: aiGateway.claude.binary", "low"),
    ("device: {grouping: {assign: {effort: hgh}}}\n", {}, "invalid: device.grouping.assign.effort", "low"),
    ("", {"PERFREPAIR_EFFORT": "hgh"}, "invalid: device.grouping.assign.effort", "low"),
])
def test_a_bad_gateway_key_from_the_file_or_env_warns_once_and_spawns(tmp_path, monkeypatch, caplog, text, environ, prefix, effort):
    for key, value in environ.items():
        monkeypatch.setenv(key, value)
    convos = spawned(tmp_path, text)
    [warned] = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert warned.startswith(prefix) and convos.identity.effort == effort


def test_a_bad_flag_for_a_gateway_key_is_an_error_not_a_fallback(tmp_path):
    assert error(tmp_path, argv=["--effort", "hgh"]).startswith("invalid: device.grouping.assign.effort")
    assert error(tmp_path, argv=["--auth", "x"]).startswith("invalid: ")


def test_dry_run_ignores_the_keys_it_does_not_have(tmp_path):
    assert spawned(tmp_path, argv=["--agent", "dry-run", "--effort", "whatever", "--auth", "x", "--model", "m"]).conversations is DRY


@dataclass(frozen=True)
class FakeSettings:
    colour: str = "red"
    effort: str = "tiny"

    def __post_init__(self):
        check_one_of("colour", self.colour, ("red", "blue"))
        if self.effort not in ("tiny", "huge"):
            raise Invalid("effort", self.effort, "tiny or huge")


class FakeConversations(ScriptedConversations):
    def __init__(self, values):
        super().__init__(lambda *_: {"colour": values.colour})
        self.values = values


FAKE = Gateway("fake", FakeSettings, lambda values, _dry: FakeConversations(values), lambda _: "FAKE_SECRET")


def test_a_new_provider_is_one_registry_row_and_a_yaml_block(tmp_path, monkeypatch):
    monkeypatch.setitem(registry.GATEWAYS, "fake", FAKE)
    monkeypatch.setenv("FAKE_SECRET", "x")
    text = "aiGateway:\n  use: fake\n  fake: {colour: blue}\ndevice:\n  grouping:\n    assign: {effort: huge}\n"
    convos = spawned(tmp_path, text)
    assert convos.conversations.values == FakeSettings("blue", "huge")
    assert json.loads(convos.start(SYSTEM, {}).ask(task("x")).text) == {"colour": "blue"}
    assert (convos.identity.gateway, convos.identity.model, convos.identity.effort) == ("fake", None, "huge")
    assert spawned(tmp_path, "aiGateway: {use: fake, fake: {colour: green}}\n", role=APPS_AGENT).conversations.values.colour == "red"
    assert spawned(tmp_path, "aiGateway: {use: claude, fake: {effort: bad}}\n").identity.gateway == "claude"
    monkeypatch.delenv("FAKE_SECRET")
    assert error(tmp_path, text).startswith("missing_secret: FAKE_SECRET: gateway fake")


def _help():
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role=APPS_AGENT)
    return ap.format_help()


@pytest.fixture
def run(tmp_path):
    run = tmp_path / "run"
    assert inbound(["--device-results", str(with_results(run))]) == 0
    assert grouping(["build", "--device-results", str(with_results(run))]) == 0
    return run


@pytest.mark.parametrize("command, argv", [
    (grouping, ["assign", "--device-results", "{run}"]),
    (ai, ["worthiness", "--device-results", "{run}", "--perf-mode", "latency"]),
    (ai, ["replace", "--device-results", "{run}", "--app", "x"]),
    (guide, ["--app", "{run}", "--device-results", "{run}"]),
])
def test_every_model_command_refuses_a_missing_secret_before_any_work(run, tmp_path, capsys, command, argv):
    before = sorted(p for p in run.rglob("*"))
    config = tmp_path / "c.yaml"
    config.write_text("aiGateway: {claude: {auth: api}}\n")
    capsys.readouterr()
    assert command([*[a.replace("{run}", str(run)) for a in argv], "--perfrepair-config", str(config)]) == 1
    err = [line for line in capsys.readouterr().err.splitlines() if not line.startswith("setting ")]
    assert len(err) == 1 and err[0].startswith("error missing_secret: ANTHROPIC_API_KEY")
    assert sorted(p for p in run.rglob("*")) == before


def test_build_with_ai_review_refuses_before_any_work(tmp_path, capsys):
    run, config = tmp_path / "run", tmp_path / "c.yaml"
    assert inbound(["--device-results", str(with_results(run))]) == 0
    config.write_text("device: {screening: {aiReview: true}}\naiGateway: {use: nope}\n")
    capsys.readouterr()
    assert grouping(["build", "--device-results", str(with_results(run)), "--perfrepair-config", str(config)]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error unknown_gateway: nope ")
    assert not (run / "grouping").exists()


def test_the_cli_gets_timeouts_claude_or_its_generous_default(tmp_path):
    assert spawned(tmp_path, "aiGateway: {use: claude}\ntimeouts: {claude: 7}\n").conversations.timeout == 7
