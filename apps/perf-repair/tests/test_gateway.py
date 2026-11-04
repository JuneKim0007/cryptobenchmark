import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
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


def test_the_default_is_claude_by_subscription_and_assign_at_low(tmp_path):
    convos = spawned(tmp_path)
    assert isinstance(convos.conversations, ClaudeCliConversations)
    assert (convos.conversations.model, convos.conversations.effort, convos.conversations.binary) == ("claude-opus-5-5", "low", "claude")
    assert (convos.identity.gateway, convos.identity.model, convos.identity.effort) == ("claude", "claude-opus-5-5", "low")
    assert spawned(tmp_path, role=APPS_AGENT).identity.effort == "medium"


def test_the_flags_reach_the_gateway_and_the_help_names_the_role_default(tmp_path):
    convos = spawned(tmp_path, argv=["--effort", "high", "--agent", "claude", "--model", "m"])
    assert isinstance(convos.conversations, ClaudeCliConversations) and (convos.conversations.effort, convos.conversations.model) == ("high", "m")
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role=GROUPING_ASSIGN)
    text = " ".join(ap.format_help().split())
    assert "$PERFREPAIR_EFFORT, aiGateway.<use>.effort, else low; claude: low, medium, high, xhigh, max" in text
    assert "$PERFREPAIR_AUTH, aiGateway.<use>.auth, else subscription; claude: subscription, api" in text
    assert "device.grouping.assign.auth" not in text and "{claude,dry-run}" in text


def test_the_binary_comes_from_the_block(tmp_path):
    assert spawned(tmp_path, "aiGateway: {claude: {binary: /bin/cc}}\n").conversations.binary == "/bin/cc"


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
    assert error(tmp_path, "aiGateway: {claude: {auth: api}}\n") == \
        "missing_secret: ANTHROPIC_API_KEY: gateway claude needs it in the environment or .env"
    assert error(tmp_path, argv=["--auth", "api"]).startswith("missing_secret")
    monkeypatch.setenv("PERFREPAIR_AUTH", "api")
    assert error(tmp_path).startswith("missing_secret")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    convos = spawned(tmp_path).conversations
    assert isinstance(convos, ClaudeConversations) and convos.client.model == "claude-opus-5-5"


def test_a_dotenv_secret_is_enough(tmp_path, monkeypatch):
    pytest.importorskip("anthropic")
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=x\n")
    monkeypatch.setattr(dotenv, "ENV_FILE", tmp_path / ".env")
    assert isinstance(spawned(tmp_path, argv=["--auth", "api"]).conversations, ClaudeConversations)


def test_subscription_never_asks_for_the_secret(tmp_path):
    assert isinstance(spawned(tmp_path, argv=["--auth", "subscription"]).conversations, ClaudeCliConversations)


def test_a_missing_sdk_is_one_coded_line(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setitem(sys.modules, "anthropic", None)
    with pytest.raises(AgentFailed, match="^claude_api_missing: "):
        spawned(tmp_path, argv=["--auth", "api"])


@pytest.mark.parametrize("text, environ, message", [
    ("aiGateway: {use: gemini}\n", {}, "unknown_gateway: gemini (file {f} aiGateway.use), known ['claude', 'dry-run']"),
    ("device: {grouping: {assign: {gateway: gemini}}}\n", {}, "unknown_gateway: gemini (file {f} device.grouping.assign), known ['claude', 'dry-run']"),
    ("", {"PERFREPAIR_AGENT": "claude-code"}, "unknown_gateway: claude-code (env PERFREPAIR_AGENT), known ['claude', 'dry-run']"),
    ("aiGateway: {gemini: {model: m}}\n", {}, "unknown_gateway: gemini (aiGateway.gemini), known ['claude', 'dry-run']"),
    ("aiGateway: {claude: {auth: oauth}}\n", {}, "invalid: aiGateway.claude.auth oauth, one of ['subscription', 'api'] (file {f})"),
    ("aiGateway: {use: dry-run, claude: {auth: oauth}}\n", {}, "invalid: aiGateway.claude.auth oauth, one of ['subscription', 'api'] (file {f})"),
    ("aiGateway: {use: 3}\n", {}, "invalid: device.grouping.assign.gateway 3, a non-empty string (file {f} aiGateway.use)"),
    ("", {"PERFREPAIR_AUTH": "x"}, "invalid: device.grouping.assign.auth x, one of ['subscription', 'api'] (env PERFREPAIR_AUTH)"),
])
def test_every_settings_error_at_spawn_is_one_coded_line(tmp_path, monkeypatch, text, environ, message):
    for key, value in environ.items():
        monkeypatch.setenv(key, value)
    assert error(tmp_path, text) == message.replace("{f}", str(tmp_path / "c.yaml"))


EFFORTS = "one of ['low', 'medium', 'high', 'xhigh', 'max']"


@pytest.mark.parametrize("text, environ, line, effort", [
    ("aiGateway: {claude: {effrt: low}}\n", {}, "unknown_key: aiGateway.claude.effrt, known ['auth', 'model', 'effort', 'binary'] (file {f})", "low"),
    ("aiGateway: {dry-run: {model: m}}\n", {}, "unknown_key: aiGateway.dry-run.model, known [] (file {f})", "low"),
    ("aiGateway: {claude: {effort: hgh}}\n", {}, f"invalid: aiGateway.claude.effort hgh, {EFFORTS}; ignored (file {{f}})", "low"),
    ("aiGateway: {use: dry-run, claude: {effort: hgh}}\n", {}, f"invalid: aiGateway.claude.effort hgh, {EFFORTS}; ignored (file {{f}})", None),
    ("aiGateway: {claude: {binary: 3}}\n", {}, "invalid: aiGateway.claude.binary 3, a non-empty string; ignored (file {f})", "low"),
    ("device: {grouping: {assign: {effort: hgh}}}\n", {}, f"invalid: device.grouping.assign.effort hgh, {EFFORTS}; using the default low (file {{f}} device.grouping.assign)", "low"),
    ("", {"PERFREPAIR_EFFORT": "hgh"}, f"invalid: device.grouping.assign.effort hgh, {EFFORTS}; using the default low (env PERFREPAIR_EFFORT)", "low"),
])
def test_a_bad_gateway_key_from_the_file_or_env_warns_once_and_spawns(tmp_path, monkeypatch, caplog, text, environ, line, effort):
    for key, value in environ.items():
        monkeypatch.setenv(key, value)
    convos = spawned(tmp_path, text)
    warned = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert warned == [line.replace("{f}", str(tmp_path / "c.yaml"))] and convos.identity.effort == effort


def test_a_bad_flag_for_a_gateway_key_is_an_error_not_a_fallback(tmp_path):
    assert error(tmp_path, argv=["--effort", "hgh"]).startswith("invalid: device.grouping.assign.effort hgh, ")
    assert error(tmp_path, argv=["--effort", "hgh"]).endswith("(cli)")
    assert error(tmp_path, argv=["--auth", "x"]).endswith("(cli)")


def test_dry_run_ignores_the_keys_it_does_not_have(tmp_path):
    assert spawned(tmp_path, argv=["--agent", "dry-run", "--effort", "whatever", "--auth", "x", "--model", "m"]).conversations is DRY


def test_the_example_file_spawns_the_code_defaults(tmp_path):
    convos = spawned(tmp_path, EXAMPLE.read_text()).conversations
    assert (convos.model, convos.effort, convos.binary) == ("claude-opus-5-5", "low", "claude")
    document = yaml.safe_load(EXAMPLE.read_text())
    assert document["aiGateway"]["use"] is None and not any(document["aiGateway"]["claude"].values())


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
    assert "{claude,dry-run,fake}" in _help()
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
    (grouping, ["report", "--device-results", "{run}", "--supervisor"]),
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
    assert err == ["error missing_secret: ANTHROPIC_API_KEY: gateway claude needs it in the environment or .env"]
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
    assert spawned(tmp_path, "aiGateway: {use: claude}\n").conversations.timeout == 3600
    assert spawned(tmp_path, "aiGateway: {use: claude}\ntimeouts: {claude: 7}\n").conversations.timeout == 7
