import argparse
import logging
from dataclasses import fields

import pytest

from perfrepair.ai.runtime.gateway.args import add_agent_args
from perfrepair.ai.runtime.gateway.claude import ClaudeSettings
from perfrepair.config import load as load_module
from perfrepair.ai.__main__ import main as ai_main
from perfrepair.config.args import fill, load_settings, positive_int
from perfrepair.config.load import config_file, load
from perfrepair.config.settings import ConfigError
from perfrepair.grouping.__main__ import main as grouping_main
from perfrepair.guide.command import parser as guide_parser
from perfrepair.inputs.check import check_any, check_text
from perfrepair.inputs.table import (AI_GATEWAY_KEY, AI_GATEWAY_USE, APPS_AGENT, APPS_REPLACE, GROUPING_ASSIGN, GROUPING_LIMIT,
                                     GROUPING_SESSIONS, GROUPING_SUPERVISOR, GROUPING_TURNS, PATHS_RESULTS, WORTHINESS)


def write(path, text):
    path.write_text(text)
    return path


def claude_values(loaded, role, **cli):
    block = loaded.settings.blocks.get("claude", {})
    return {f.name: loaded.role_value(role, f.name, AI_GATEWAY_KEY, cli.get(f.name), (block.get(f.name), "aiGateway.claude"),
                                      f.default, check_any) for f in fields(ClaudeSettings)}


def gateway_name(loaded, role, cli, default):
    use = loaded.settings.get(AI_GATEWAY_USE.key)
    return loaded.role_value(role, "gateway", AI_GATEWAY_USE, cli, (use, AI_GATEWAY_USE.key), default, check_text)


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
    bad = write(tmp_path / "c.yaml", "aiGateway: 3\n")
    with pytest.raises(ConfigError, match=r"^invalid: aiGateway 3, .*c.yaml\)$"):
        load(bad, {}, {})
    with pytest.raises(ConfigError, match=r"^invalid_yaml: .*y.yaml: .* at line \d+ column \d+\s*\Z") as e:
        load(write(tmp_path / "y.yaml", "agent: [\n"), {}, {})
    assert "\n" not in str(e.value)


def test_agent_precedence_is_cli_env_block_dotenv_default_with_sources(tmp_path):
    f = write(tmp_path / "c.yaml", "aiGateway: {use: claude, claude: {model: file-model, effort: low}}\n")
    loaded = load(f, {"PERFREPAIR_MODEL": "env-model"}, {"PERFREPAIR_MODEL": "dot", "PERFREPAIR_EFFORT": "max",
                                                         "PERFREPAIR_AGENT": "dry-run"})
    assert gateway_name(loaded, APPS_REPLACE, "dry-run", "x") == "dry-run"
    assert claude_values(loaded, APPS_REPLACE) == {"auth": "subscription", "model": "env-model", "effort": "low", "binary": "claude"}
    assert loaded.sources == {"apps.replace.gateway": "cli", "apps.replace.auth": "default", "apps.replace.binary": "default",
                              "apps.replace.model": "env PERFREPAIR_MODEL", "apps.replace.effort": f"file {f} aiGateway.claude"}
    no_file = load(None, {}, {"PERFREPAIR_EFFORT": "max", "PERFREPAIR_AGENT": "dry-run"})
    assert claude_values(no_file, APPS_REPLACE)["effort"] == "max" and no_file.sources["apps.replace.effort"] == ".env PERFREPAIR_EFFORT"
    assert gateway_name(no_file, APPS_REPLACE, None, "x") == "dry-run"
    assert gateway_name(load(f, {}, {"PERFREPAIR_AGENT": "dry-run"}), APPS_REPLACE, None, "x") == "claude"


def test_a_role_key_beats_the_block_from_every_layer_and_other_keys_fall_back(tmp_path):
    f = write(tmp_path / "c.yaml", "aiGateway: {claude: {model: shared, binary: /opt/claude}}\n"
                                   "device: {grouping: {assign: {effort: xhigh, gateway: dry-run}}}\napps: {agent: {model: guide-model}}\n")
    loaded = load(f, {"PERFREPAIR_EFFORT": "low", "PERFREPAIR_AGENT": "claude"}, {})
    assert claude_values(loaded, GROUPING_ASSIGN) == {"auth": "subscription", "model": "shared", "effort": "xhigh", "binary": "/opt/claude"}
    assert gateway_name(loaded, GROUPING_ASSIGN, None, "x") == "dry-run"
    assert loaded.sources["device.grouping.assign.effort"] == f"file {f} device.grouping.assign"
    assert claude_values(loaded, APPS_AGENT)["model"] == "guide-model" and claude_values(loaded, WORTHINESS)["effort"] == "low"
    assert claude_values(loaded, GROUPING_ASSIGN, effort="medium")["effort"] == "medium"


def test_a_role_section_never_supplies_a_gateway_only_key(tmp_path):
    loaded = load(write(tmp_path / "c.yaml", "apps: {agent: {auth: api}}\n"), {}, {})
    assert claude_values(loaded, APPS_AGENT)["auth"] == "subscription"


def test_assign_defaults_low_and_the_supervisor_has_no_special_default():
    defaults = load(None, {}, {})
    assert claude_values(defaults, GROUPING_ASSIGN)["effort"] == "low"
    assert defaults.sources["device.grouping.assign.effort"] == "default device.grouping.assign"
    assert claude_values(defaults, GROUPING_SUPERVISOR)["effort"] == "medium" and claude_values(defaults, APPS_AGENT)["effort"] == "medium"


@pytest.mark.parametrize("environ, dot, text, source", [
    ({"PERFREPAIR_EFFORT": "max"}, {}, "", "env PERFREPAIR_EFFORT"),
    ({}, {}, "aiGateway: {claude: {effort: max}}\n", "aiGateway.claude"),
    ({}, {"PERFREPAIR_EFFORT": "max"}, "", ".env PERFREPAIR_EFFORT")])
def test_every_gateway_wide_layer_raises_every_role_including_assign(tmp_path, environ, dot, text, source):
    loaded = load(write(tmp_path / "c.yaml", text), environ, dot)
    assert claude_values(loaded, GROUPING_ASSIGN)["effort"] == claude_values(loaded, GROUPING_SUPERVISOR)["effort"] == "max"
    assert loaded.sources["device.grouping.assign.effort"].endswith(source)


def test_a_role_section_or_the_flag_sets_one_role_above_every_gateway_wide_layer(tmp_path):
    f = write(tmp_path / "c.yaml", "aiGateway: {claude: {effort: max}}\ndevice: {grouping: {assign: {effort: medium}}}\n")
    loaded = load(f, {"PERFREPAIR_EFFORT": "xhigh"}, {})
    assert claude_values(loaded, GROUPING_ASSIGN)["effort"] == "medium"
    assert claude_values(loaded, GROUPING_SUPERVISOR)["effort"] == "xhigh"
    assert claude_values(loaded, GROUPING_ASSIGN, effort="low")["effort"] == "low"


@pytest.mark.parametrize("flag", (["--agent", "dry-run"], ["--auth", "api"], ["--model", "m"], ["--effort", "low"], ["--prompts", "p"]))
def test_build_refuses_a_model_flag_when_it_calls_no_model(tmp_path, capsys, flag):
    with pytest.raises(SystemExit) as e:
        grouping_main(["build", "--device-results", str(tmp_path), *flag])
    assert e.value.code == 2 and f"{flag[0]} only apply with device.screening.aiReview" in capsys.readouterr().err


@pytest.mark.parametrize("step", (["build"], ["interop-plan"], ["interop-read", "--results", "r"]))
def test_every_grouping_step_takes_the_device_from_the_settings_file(tmp_path, capsys, step):
    with pytest.raises(SystemExit) as e:
        grouping_main(step)
    assert e.value.code == 2 and "--device-results (or paths.results in perfrepair.yaml)" in capsys.readouterr().err
    (tmp_path / "there" / "only-device").mkdir(parents=True)
    write(tmp_path / "there" / "only-device" / "manifest.yaml", "schemaVersion: 1\n")
    f = write(tmp_path / "c.yaml", "paths: {results: there}\n")
    assert grouping_main([*step, "--perfrepair-config", str(f)]) == 1


def test_fill_keeps_cli_values_then_file_then_code_default_and_records_the_source(tmp_path):
    f = write(tmp_path / "c.yaml", "paths: {results: r}\ndevice: {grouping: {turns: 5}}\n")
    loaded = load(f, {}, {})
    args = argparse.Namespace(results=None, turns=None, sessions=None, limit=7)
    fill(loaded, args, {"results": PATHS_RESULTS, "turns": GROUPING_TURNS, "sessions": GROUPING_SESSIONS, "limit": GROUPING_LIMIT})
    assert (args.results, args.turns, args.sessions, args.limit) == (tmp_path / "r", 5, 2, 7)
    assert loaded.sources == {"paths.results": f"file {f}", "device.grouping.turns": f"file {f}", "device.grouping.sessions": "default",
                              "device.grouping.limit": "cli"}


def test_a_bad_file_exits_2_with_the_error_line(tmp_path, capsys):
    ap = argparse.ArgumentParser()
    add_agent_args(ap, role=APPS_AGENT)
    args = ap.parse_args(["--perfrepair-config", str(write(tmp_path / "c.yaml", "aiGateway: {claude: {token: x}}\n"))])
    with pytest.raises(SystemExit) as e:
        load_settings(ap, args)
    assert e.value.code == 2 and "secret_key: aiGateway.claude.token" in capsys.readouterr().err


def test_a_command_without_a_device_folder_or_a_results_root_exits_2(capsys):
    with pytest.raises(SystemExit) as e:
        grouping_main(["assign", "--agent", "dry-run"])
    assert e.value.code == 2 and "--device-results (or paths.results in perfrepair.yaml)" in capsys.readouterr().err


@pytest.mark.parametrize("command", ((grouping_main, ["assign", "--device-results", "r"]),
                                     (ai_main, ["worthiness", "--device-results", "r", "--mode", "latency"])))
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
    f.write_text("device: {grouping: {turns: 4}}\n")
    loaded = load(f, {}, {})
    with caplog.at_level(logging.DEBUG, logger="perfrepair"):
        loaded.read(GROUPING_TURNS)
        loaded.read(GROUPING_TURNS)
        loaded.read(GROUPING_SESSIONS)
        claude_values(loaded, APPS_REPLACE, model="m")
    lines = caplog.messages
    assert lines.count(f"setting device.grouping.turns: 4 (file {f})") == 1
    assert "setting device.grouping.sessions: 2 (default)" in lines and "setting apps.replace.model: m (cli)" in lines
    assert len(lines) == 2 + len(fields(ClaudeSettings))
    shown = [r.getMessage() for r in caplog.records if r.levelno >= logging.INFO]
    assert shown == [f"setting device.grouping.turns: 4 (file {f})"]
