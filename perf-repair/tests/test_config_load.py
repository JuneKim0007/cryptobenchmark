import argparse
import logging
from dataclasses import fields

import pytest

from perfrepair.ai.runtime.agent import ClaudeCodeConversations
from perfrepair.ai.runtime.agent.select import add_agent_args, conversations
from perfrepair.config import dotenv, load as load_module
from perfrepair.ai.__main__ import main as ai_main
from perfrepair.config.args import fill, load_settings, positive_int
from perfrepair.config.load import config_file, load
from perfrepair.config.settings import Agent, ConfigError
from perfrepair.grouping.__main__ import main as grouping_main
from perfrepair.guide.command import parser as guide_parser

DRY = object()


def write(path, text):
    path.write_text(text)
    return path


def test_lookup_order_is_flag_then_env_then_the_package_file(tmp_path, monkeypatch):
    flag, env, default = (write(tmp_path / n, "{}") for n in ("flag.yaml", "env.yaml", "perfrepair.yaml"))
    monkeypatch.setattr(load_module, "DEFAULT_FILE", default)
    assert config_file(flag, {"PERFREPAIR_CONFIG": str(env)}) == flag.resolve()
    assert config_file(None, {"PERFREPAIR_CONFIG": str(env)}) == env.resolve()
    assert config_file(None, {}) == default
    default.unlink()
    assert config_file(None, {}) is None


def test_a_named_file_that_is_missing_is_an_error(tmp_path):
    with pytest.raises(ConfigError, match=r"missing_file: .*nope.yaml \(--perfrepair-config\)"):
        config_file(tmp_path / "nope.yaml", {})
    with pytest.raises(ConfigError, match=r"\(PERFREPAIR_CONFIG\)"):
        config_file(None, {"PERFREPAIR_CONFIG": str(tmp_path / "nope.yaml")})


def test_file_errors_name_the_file(tmp_path):
    bad = write(tmp_path / "c.yaml", "agent: {effort: hgh}\n")
    with pytest.raises(ConfigError, match=r"^invalid: agent.effort hgh, .*c.yaml\)$"):
        load(bad, {}, {})
    with pytest.raises(ConfigError, match=r"^invalid_yaml: .*y.yaml: .* at line \d+ column \d+\s*\Z") as e:
        load(write(tmp_path / "y.yaml", "agent: [\n"), {}, {})
    assert "\n" not in str(e.value)
    with pytest.raises(ConfigError, match="^invalid: PERFREPAIR_EFFORT hgh"):
        load(None, {"PERFREPAIR_EFFORT": "hgh"}, {})
    with pytest.raises(ConfigError, match="^invalid: .env PERFREPAIR_AGENT x"):
        load(None, {}, {"PERFREPAIR_AGENT": "x"})


def test_agent_precedence_is_cli_env_file_dotenv_default_with_sources(tmp_path):
    f = write(tmp_path / "c.yaml", "agent: {backend: claude, model: file-model, effort: low}\n")
    loaded = load(f, {"PERFREPAIR_MODEL": "env-model"}, {"PERFREPAIR_MODEL": "dot", "PERFREPAIR_EFFORT": "max",
                                                         "PERFREPAIR_AGENT": "dry-run"})
    a = loaded.agent("ai.replace", {"backend": "dry-run", "model": None, "effort": None})
    assert a == Agent("dry-run", "env-model", "low", "claude")
    assert loaded.sources == {"ai.replace.backend": "cli", "ai.replace.model": "env PERFREPAIR_MODEL",
                              "ai.replace.effort": f"file {f} agent", "ai.replace.claudeBinary": "default"}
    no_file = load(None, {}, {"PERFREPAIR_EFFORT": "max"})
    assert no_file.agent("ai.replace", {}).effort == "max" and no_file.sources["ai.replace.effort"] == ".env PERFREPAIR_EFFORT"


def test_a_role_key_beats_agent_from_every_layer_and_other_keys_fall_back(tmp_path):
    f = write(tmp_path / "c.yaml", "agent: {model: shared, claudeBinary: /opt/claude}\n"
                                   "grouping: {assign: {effort: xhigh}}\nguide: {agent: {model: guide-model}}\n")
    loaded = load(f, {"PERFREPAIR_EFFORT": "low"}, {})
    assert loaded.agent("grouping.assign", {}) == Agent("claude-code", "shared", "xhigh", "/opt/claude")
    assert loaded.sources["grouping.assign.effort"] == f"file {f} grouping.assign"
    assert loaded.agent("guide", {}).model == "guide-model" and loaded.agent("ai.worthiness", {}).effort == "low"
    assert loaded.agent("grouping.assign", {"effort": "medium"}).effort == "medium"


def test_assign_defaults_low_and_the_supervisor_has_no_special_default():
    defaults = load(None, {}, {})
    assert defaults.agent("grouping.assign", {}).effort == "low"
    assert defaults.sources["grouping.assign.effort"] == "default grouping.assign"
    assert defaults.agent("grouping.supervisor", {}).effort == "medium" and defaults.agent("guide", {}).effort == "medium"


@pytest.mark.parametrize("environ, dot, text, source", [
    ({"PERFREPAIR_EFFORT": "max"}, {}, "", "env PERFREPAIR_EFFORT"),
    ({}, {}, "agent: {effort: max}\n", "agent"),
    ({}, {"PERFREPAIR_EFFORT": "max"}, "", ".env PERFREPAIR_EFFORT")])
def test_every_agent_wide_layer_raises_every_role_including_assign(tmp_path, environ, dot, text, source):
    loaded = load(write(tmp_path / "c.yaml", text), environ, dot)
    assert loaded.agent("grouping.assign", {}).effort == loaded.agent("grouping.supervisor", {}).effort == "max"
    assert loaded.sources["grouping.assign.effort"].endswith(source)


def test_a_role_section_or_the_flag_sets_one_role_above_every_agent_wide_layer(tmp_path):
    f = write(tmp_path / "c.yaml", "agent: {effort: max}\ngrouping: {assign: {effort: medium}}\n")
    loaded = load(f, {"PERFREPAIR_EFFORT": "xhigh"}, {})
    assert loaded.agent("grouping.assign", {}).effort == "medium"
    assert loaded.agent("grouping.supervisor", {}).effort == "xhigh"
    assert loaded.agent("grouping.assign", {"effort": "low"}).effort == "low"


@pytest.mark.parametrize("flag", (["--agent", "dry-run"], ["--model", "m"], ["--effort", "low"], ["--prompts", "p"]))
def test_build_refuses_a_model_flag_when_it_calls_no_model(tmp_path, capsys, flag):
    with pytest.raises(SystemExit) as e:
        grouping_main(["build", "--manifest", "m", "--run", str(tmp_path), *flag])
    assert e.value.code == 2 and f"{flag[0]} only apply with screening.aiReview" in capsys.readouterr().err


@pytest.mark.parametrize("step", (["build", "--manifest", "m"], ["interop-plan"], ["interop-read", "--results", "r"]))
def test_every_grouping_step_takes_the_run_from_the_settings_file(tmp_path, capsys, step):
    with pytest.raises(SystemExit) as e:
        grouping_main(step)
    assert e.value.code == 2 and "--run (or paths.run in perfrepair.yaml)" in capsys.readouterr().err
    f = write(tmp_path / "c.yaml", "paths: {run: there}\n")
    assert grouping_main([*step, "--perfrepair-config", str(f)]) == 1


def test_the_flag_reaches_the_backend_and_the_help_names_the_role_default():
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role="grouping.assign")
    args = ap.parse_args(["--effort", "high", "--agent", "claude-code"])
    convos = conversations(args, load_settings(ap, args), DRY)
    assert isinstance(convos, ClaudeCodeConversations) and convos.effort == "high"
    assert "$PERFREPAIR_EFFORT, agent.effort, else low" in " ".join(ap.format_help().split())


def test_assign_takes_the_environment_effort_and_dotenv_fills_the_backend(tmp_path, monkeypatch):
    monkeypatch.setattr(dotenv, "ENV_FILE", write(tmp_path / ".env", "PERFREPAIR_AGENT=dry-run\n"))
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role="grouping.assign")
    args = ap.parse_args([])
    assert conversations(args, load_settings(ap, args), DRY) is DRY


def test_claude_binary_reaches_the_claude_code_backend(tmp_path):
    f = write(tmp_path / "c.yaml", "agent: {backend: claude-code}\ngrouping: {supervisor: {claudeBinary: /bin/cc}}\n")
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role="grouping.supervisor")
    args = ap.parse_args(["--perfrepair-config", str(f)])
    assert conversations(args, load_settings(ap, args), DRY).binary == "/bin/cc"


def test_fill_keeps_cli_values_then_file_then_code_default_and_records_the_source(tmp_path):
    f = write(tmp_path / "c.yaml", "paths: {run: r}\ngrouping: {turns: 5}\n")
    loaded = load(f, {}, {})
    args = argparse.Namespace(run=None, turns=None, sessions=None, limit=7)
    fill(loaded, args, {"run": ("paths.run", None), "turns": ("grouping.turns", 3), "sessions": ("grouping.sessions", 2),
                        "limit": ("grouping.limit", None)})
    assert (args.run, args.turns, args.sessions, args.limit) == (tmp_path / "r", 5, 2, 7)
    assert loaded.sources == {"paths.run": f"file {f}", "grouping.turns": f"file {f}", "grouping.sessions": "default",
                              "grouping.limit": "cli"}


def test_a_bad_file_exits_2_with_the_error_line(tmp_path, capsys):
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role="guide")
    args = ap.parse_args(["--perfrepair-config", str(write(tmp_path / "c.yaml", "agent: {token: x}\n"))])
    with pytest.raises(SystemExit) as e:
        load_settings(ap, args)
    assert e.value.code == 2 and "secret_key: agent.token" in capsys.readouterr().err


def test_a_command_without_run_and_without_paths_run_exits_2(capsys):
    with pytest.raises(SystemExit) as e:
        grouping_main(["assign", "--agent", "dry-run"])
    assert e.value.code == 2 and "--run (or paths.run in perfrepair.yaml)" in capsys.readouterr().err


@pytest.mark.parametrize("command", ((grouping_main, ["assign", "--run", "r"]),
                                     (ai_main, ["worthiness", "--run", "r", "--mode", "latency"])))
@pytest.mark.parametrize("flag", ("--turns", "--sessions", "--limit"))
@pytest.mark.parametrize("value", ("0", "-1", "x", "1.5"))
def test_a_count_flag_takes_only_a_positive_integer(command, flag, value, capsys):
    main, arguments = command
    with pytest.raises(SystemExit) as e:
        main([*arguments, f"{flag}={value}"])
    assert e.value.code == 2 and "is not a positive integer" in capsys.readouterr().err


def test_the_guide_limit_takes_only_a_positive_integer(capsys):
    with pytest.raises(SystemExit):
        guide_parser().parse_args(["--limit", "0"])
    assert "is not a positive integer" in capsys.readouterr().err
    assert positive_int("3") == 3


def test_each_resolved_setting_is_logged_once_with_its_source(tmp_path, caplog):
    f = tmp_path / "perfrepair.yaml"
    f.write_text("grouping: {turns: 4}\n")
    loaded = load(f, {}, {})
    with caplog.at_level(logging.DEBUG, logger="perfrepair"):
        loaded.value("grouping.turns")
        loaded.value("grouping.turns")
        loaded.value("grouping.sessions", default=2)
        loaded.agent("ai.replace", {"model": "m"})
    lines = caplog.messages
    assert lines.count(f"setting grouping.turns: 4 (file {f})") == 1
    assert "setting grouping.sessions: 2 (default)" in lines and "setting ai.replace.model: m (cli)" in lines
    assert len(lines) == 2 + len(fields(Agent))
    shown = [r.getMessage() for r in caplog.records if r.levelno >= logging.INFO]
    assert shown == [f"setting grouping.turns: 4 (file {f})"]
