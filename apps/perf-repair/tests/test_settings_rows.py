"""Each settings policy's behaviour: use-default, error, budgets and bad values."""
import logging

import pytest
import yaml

from perfrepair.config.load import load
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.guide.command import main as guide
from perfrepair.inputs import table
from perfrepair.inputs.check import check_positive
from perfrepair.inputs.resolve import Candidate, InputError, OnInvalid, choose
from perfrepair.inputs.table import ROWS, RoleRow


ROLES = [r for r in ROWS if isinstance(r, RoleRow)]


@pytest.mark.parametrize("role", ROLES, ids=lambda r: r.key)
def test_every_role_has_one_budget_a_file_may_set(tmp_path, caplog, role):
    assert role.budget_row.key == f"{role.key}.budget" and role.budget_row.default == role.budget > 0
    *sections, leaf = role.key.split(".")
    document = {leaf: {"budget": 123}}
    for section in reversed(sections):
        document = {section: document}
    assert load(write(tmp_path, yaml.safe_dump(document)), {}, {}).read(role.budget_row) == 123
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_a_bad_budget_warns_and_keeps_the_role_default(tmp_path, caplog):
    loaded = load(write(tmp_path, "device: {grouping: {assign: {budget: 0}}}\n"), {}, {})
    assert loaded.read(table.GROUPING_ASSIGN.budget_row) == table.GROUPING_ASSIGN.budget
    assert any(m.startswith("invalid: device.grouping.assign.budget 0") for m in caplog.messages)


def picked(on_invalid, value, source="file c.yaml"):
    return choose("device.grouping.turns", [Candidate(value, source), Candidate(3, "default", explicit=False)],
                  check_positive, on_invalid)


def test_use_default_warns_in_one_line_and_takes_the_default(caplog):
    assert picked(OnInvalid.USE_DEFAULT, "abc").value == 3
    [record] = caplog.records
    assert record.levelno == logging.WARNING and record.code == "invalid" and record.source == "file c.yaml"


def test_use_default_without_a_default_ignores_the_value(caplog):
    assert choose("x", [Candidate(0, "env X")], check_positive, OnInvalid.USE_DEFAULT) is None
    assert [m.split(":")[0] for m in caplog.messages] == ["invalid"]


def test_error_refuses_with_the_source_and_no_warning(caplog):
    with pytest.raises(InputError) as e:
        picked(OnInvalid.ERROR, "abc")
    assert e.value.code == "invalid" and caplog.records == []


def test_a_bad_flag_is_an_error_under_either_policy():
    with pytest.raises(InputError, match=r"\(cli\)$"):
        picked(OnInvalid.USE_DEFAULT, "abc", "cli")


def test_a_bad_code_default_is_never_hidden():
    with pytest.raises(InputError):
        choose("x", [Candidate("abc", "default", explicit=False)], check_positive, OnInvalid.USE_DEFAULT)


def write(tmp_path, text):
    path = tmp_path / "c.yaml"
    path.write_text(text)
    return path


@pytest.mark.parametrize("key, text, value", [
    (table.GROUPING_TURNS, "device: {grouping: {turns: abc}}\n", 3),
    (table.GROUPING_SESSIONS, "device: {grouping: {sessions: 0}}\n", 2),
    (table.GROUPING_LIMIT, "device: {grouping: {limit: -1}}\n", None),
    (table.APPS_LIMIT, "apps: {limit: x}\n", None),
    (table.APPS_TARGETS, "apps: {targets: 3}\n", None),
    (table.APPS_TARGETS, "apps: {targets: [{name: a}]}\n", None),
    (table.GROUPING_NO_RERUN, "device: {grouping: {noRerun: maybe}}\n", True),
    (table.APPS_DEVICE, "apps: {device: 'yes'}\n", False),
    (table.SCREENING_AI_REVIEW, "device: {screening: {aiReview: 'yes'}}\n", False),
    (table.PATHS_PROMPTS, "paths: {prompts: ''}\n", None),
])
def test_a_bad_file_value_warns_once_and_reads_the_default(tmp_path, caplog, key, text, value):
    loaded = load(write(tmp_path, text), {}, {})
    assert loaded.read(key) == value and loaded.read(key) == value
    # a command's logger passes DEBUG on to events.jsonl; the warning is the one line at INFO or above
    shown = [r.getMessage() for r in caplog.records if r.levelno >= logging.INFO]
    assert len(shown) == 1 and shown[0].startswith(f"invalid: {key.key} ")
    assert loaded.sources[key.key] == "default"


def test_a_bad_perf_mode_in_the_file_warns_and_a_bad_flag_is_argparse(tmp_path, capsys):
    config = write(tmp_path, "apps: {perfMode: [fast]}\n")
    code = guide(["--app", str(tmp_path), "--device-results", str(tmp_path), "--agent", "dry-run",
                  "--perfrepair-config", str(config)])
    err = capsys.readouterr().err
    assert code == 1 and "invalid: apps.perfMode" in err
    with pytest.raises(SystemExit) as e:
        guide(["--app", "a", "--perf-mode", "fast"])
    assert e.value.code == 2


def test_a_catalog_that_is_no_path_stops_the_step(tmp_path, capsys):
    config = write(tmp_path, "device: {screening: {catalog: 3}}\n")
    assert grouping(["build", "--device-results", str(tmp_path), "--perfrepair-config", str(config)]) == 1
    assert capsys.readouterr().err.splitlines()[-1].startswith("error invalid: device.screening.catalog")


def test_a_malformed_setting_warns_and_the_command_proceeds(tmp_path, capsys):
    config = write(tmp_path, "device: {grouping: {turns: abc}}\n")
    assert grouping(["assign", "--device-results", str(tmp_path), "--agent", "dry-run", "--perfrepair-config", str(config)]) == 1
    err = capsys.readouterr().err
    assert "invalid: device.grouping.turns" in err and "invalid" not in err.splitlines()[-1]
