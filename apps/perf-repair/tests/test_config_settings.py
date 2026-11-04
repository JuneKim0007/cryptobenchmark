import logging

import pytest

from perfrepair.config.settings import ConfigError, Settings, parse, unknown_keys

ROOT_KEYS = "['aiGateway', 'paths', 'device', 'apps', 'timeouts', 'stops']"
ROLE_KEYS = "['gateway', 'model', 'effort']"


def warnings(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


def test_the_parser_holds_raw_values_for_the_rows():
    s = parse({"aiGateway": {"use": "dry-run", "claude": {"binary": "/opt/claude", "model": None}},
               "device": {"grouping": {"turns": "abc"}}}, "c.yaml")
    assert s.get("aiGateway.use") == "dry-run" and s.get("device.grouping.turns") == "abc"
    assert s.blocks == {"claude": {"binary": "/opt/claude"}}
    assert s.get("device.grouping.assign.effort") is None and s.get("device.grouping.turns.x") is None


def test_empty_file_and_null_values_are_unset():
    assert parse(None, "c.yaml") == Settings()
    assert parse({"aiGateway": None, "device": {"grouping": None}}, "c.yaml").get("device.grouping.limit") is None


@pytest.mark.parametrize("document, line", [
    ({"agnt": {}}, f"unknown_key: agnt, known {ROOT_KEYS} (c.yaml)"),
    ({"grouping": {"turns": 3}}, f"unknown_key: grouping, known {ROOT_KEYS} (c.yaml)"),
    ({"guide": {"mode": "latency"}}, f"unknown_key: guide, known {ROOT_KEYS} (c.yaml)"),
    ({"device": {"name": "x"}}, "unknown_key: device.name, known ['screening', 'grouping', 'benchmark', 'filterByApps', 'bundled', 'id', 'worthiness'] (c.yaml)"),
    ({"device": {"grouping": {"assign": {"efort": "low"}}}}, f"unknown_key: device.grouping.assign.efort, known {ROLE_KEYS} (c.yaml)"),
    ({"apps": {"agent": {"auth": "api"}}}, f"unknown_key: apps.agent.auth, known {ROLE_KEYS} (c.yaml)"),
    ({"apps": {"names": []}}, "unknown_key: apps.names, known ['targets', 'perfMode', 'limit', 'measure', 'maxChange', 'agent', 'replace'] (c.yaml)"),
])
def test_an_unknown_key_is_one_warning_naming_the_known_keys(document, line, caplog):
    parse(document, "c.yaml")
    assert warnings(caplog) == [line]


def test_a_section_that_is_not_a_mapping_warns_when_nothing_unsafe_sits_in_it(caplog):
    assert parse({"paths": 3}, "c.yaml").get("paths.prompts") is None
    assert warnings(caplog) == ["invalid: paths 3, a mapping; ignored (c.yaml)"]


@pytest.mark.parametrize("document, message", [
    ({"aiGateway": "claude"}, "invalid: aiGateway claude, a mapping"),
    ({"aiGateway": {"claude": "x"}}, "invalid: aiGateway.claude x, a mapping"),
    ({"device": {"screening": 3}}, "invalid: device.screening 3, a mapping"),
    ({"apps": {"agent": "dry-run"}}, "invalid: apps.agent dry-run, a mapping"),
    (["a"], "invalid: <root> ['a'], a mapping"),
])
def test_a_section_holding_an_error_row_must_be_a_mapping(document, message):
    with pytest.raises(ConfigError) as e:
        parse(document, "c.yaml")
    assert str(e.value) == message


@pytest.mark.parametrize("document, where", [
    ({"aiGateway": {"apiKey": "x"}}, "aiGateway.apiKey"),
    ({"aiGateway": {"claude": {"apiKey": "x"}}}, "aiGateway.claude.apiKey"),
    ({"aiGateway": {"someone": {"token": "x"}}}, "aiGateway.someone.token"),
    ({"ANTHROPIC_API_KEY": "x"}, "ANTHROPIC_API_KEY"),
    ({"apps": {"agent": {"auth_token": "x"}}}, "apps.agent.auth_token"),
    ({"aiGateway": {"claude": {"model": "sk-ant-abc"}}}, "aiGateway.claude.model"),
    ({"aiGateway": {"use": "sk-ant-abc"}}, "aiGateway.use"),
    ({"device": {"grouping": {"assign": {"model": "sk-ant-abc"}}}}, "device.grouping.assign.model"),
    ({"nowhere": {"deep": [{"password": "x"}]}}, "nowhere.deep[0].password"),
    ({"nowhere": ["sk-ant-abc"]}, "nowhere[0]"),
])
def test_a_secret_is_refused_anywhere_even_under_an_unknown_key(document, where, caplog):
    with pytest.raises(ConfigError) as e:
        parse(document, "c.yaml")
    assert str(e.value) == f"secret_key: {where}: keep secrets in the environment or .env"
    assert warnings(caplog) == []


@pytest.mark.parametrize("document, key, place", [
    ({"paths": {"results": "r"}}, "paths.results", "--results-root"),
    ({"device": {"benchmark": {"config": "g.yaml"}}}, "device.benchmark.config", "guide --config"),
    ({"apps": {"benchmarkConfig": "g.yaml"}}, "apps.benchmarkConfig", "guide --harness-config"),
    ({"run": {"id": "one"}}, "run.id", "guide --run-id"),
    ({"run": {"onExisting": "resume"}}, "run.onExisting", "guide --on-existing"),
])
def test_a_moved_key_with_a_value_names_its_new_place(document, key, place):
    with pytest.raises(ConfigError, match=f"^placement: {key} is no perfrepair.yaml key; set .*{place}"):
        parse(document, "c.yaml")


def test_a_moved_key_left_empty_sets_nothing_and_is_one_warning(caplog):
    parse({"paths": {"results": None}}, "c.yaml")
    assert warnings(caplog) == ["unknown_key: paths.results, known ['prompts'] (c.yaml)"]


def test_unknown_keys_lists_what_parse_warns_about():
    assert unknown_keys({"agnt": 1, "apps": {"names": []}, "device": {"grouping": {"assign": {"efort": "low"}}}}) == [
        "agnt", "apps.names", "device.grouping.assign.efort"]
