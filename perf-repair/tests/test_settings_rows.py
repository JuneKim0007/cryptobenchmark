"""The table against the code and the example: every row read once, every example key a row, each policy's behaviour."""
import ast
import logging
from dataclasses import fields
from pathlib import Path

import pytest
import yaml

from perfrepair.ai.runtime.engine.ask import Limits
from perfrepair.ai.runtime.gateway import registry
from perfrepair.config.load import load
from perfrepair.grouping.__main__ import main as grouping
from perfrepair.guide.command import main as guide
from perfrepair.inputs import table
from perfrepair.inputs.check import check_positive
from perfrepair.inputs.resolve import Candidate, InputError, OnInvalid, choose
from perfrepair.inputs.table import ROLE_KEYS, ROWS, RoleRow, Row
from perfrepair.result.modes import MODES

SRC = Path(table.__file__).parents[1]
EXAMPLE = Path(__file__).parents[1] / "perfrepair.example.yaml"
ERROR_ROWS = {"aiGateway.use", "aiGateway.<gateway>.auth", "device.screening.catalog", "device.id"}


def row_names():
    return [name for name, value in vars(table).items() if isinstance(value, (Row, RoleRow))]


def readers(name):
    """The modules, the table aside, whose code uses the row's constant."""
    found = []
    for path in SRC.rglob("*.py"):
        if path == Path(table.__file__):
            continue
        tree = ast.parse(path.read_text())
        if any(isinstance(n, ast.Name) and n.id == name for n in ast.walk(tree)):
            found.append(str(path.relative_to(SRC)))
    return found


def leaves(document, path=""):
    for key, value in document.items():
        where = f"{path}.{key}" if path else key
        if isinstance(value, dict) and value:
            yield from leaves(value, where)
        else:
            yield where


def row_of(key):
    """The row of an example key; a role section's own name counts as that role."""
    for row in ROWS:
        if isinstance(row, Row) and row.key == key:
            return row
        if isinstance(row, RoleRow) and key in (row.key, *(f"{row.key}.{k}" for k in ROLE_KEYS)):
            return row
    return None


@pytest.mark.parametrize("name", row_names())
def test_every_row_has_exactly_one_reader(name):
    assert len(readers(name)) == 1, f"{name}: {readers(name)}"


def test_the_reader_check_sees_a_parsed_but_unused_setting():
    assert readers("NOT_A_ROW") == [] and row_of("device.unread") is None


def test_every_example_key_is_a_row_some_command_reads():
    constants = {id(getattr(table, name)): name for name in row_names()}
    gateway_keys = {f.name for g in registry.GATEWAYS.values() for f in fields(g.settings)}
    for key in leaves(yaml.safe_load(EXAMPLE.read_text())):
        if key.startswith("aiGateway.") and key != "aiGateway.use":
            _, gateway, leaf = key.split(".")
            assert gateway in registry.GATEWAYS and leaf in gateway_keys, key
            continue
        row = row_of(key)
        assert row is not None, f"{key}: in the example, no row"
        assert readers(constants[id(row)]), f"{key}: no command reads it"


def test_every_settable_row_is_in_the_example():
    keys = set(leaves(yaml.safe_load(EXAMPLE.read_text())))
    for row in ROWS:
        if "<" not in row.key:
            assert row.key in keys, row.key


def test_only_the_unsafe_rows_refuse_a_fallback():
    assert {r.key for r in ROWS if isinstance(r, Row) and r.invalid is OnInvalid.ERROR} == ERROR_ROWS


def test_the_row_defaults_are_what_their_readers_use():
    assert (table.GROUPING_TURNS.default, table.GROUPING_SESSIONS.default) == (Limits.turns, Limits.sessions)
    assert table.APPS_MODE.default in MODES and table.GROUPING_ASSIGN.defaults == {"effort": "low"}


def picked(on_invalid, value, source="file c.yaml"):
    return choose("device.grouping.turns", [Candidate(value, source), Candidate(3, "default", explicit=False)],
                  check_positive, on_invalid)


def test_use_default_warns_in_one_line_and_takes_the_default(caplog):
    assert picked(OnInvalid.USE_DEFAULT, "abc").value == 3
    [record] = caplog.records
    assert record.levelno == logging.WARNING and record.code == "invalid" and record.source == "file c.yaml"
    assert record.getMessage() == "invalid: device.grouping.turns abc, a positive integer; using the default 3 (file c.yaml)"


def test_use_default_without_a_default_ignores_the_value(caplog):
    assert choose("x", [Candidate(0, "env X")], check_positive, OnInvalid.USE_DEFAULT) is None
    assert caplog.messages == ["invalid: x 0, a positive integer; ignored (env X)"]


def test_error_refuses_with_the_source_and_no_warning(caplog):
    with pytest.raises(InputError) as e:
        picked(OnInvalid.ERROR, "abc")
    assert e.value.code == "invalid" and caplog.records == []
    assert str(e.value) == "invalid: device.grouping.turns abc, a positive integer (file c.yaml)"


def test_a_bad_flag_is_an_error_under_either_policy():
    with pytest.raises(InputError, match=r"\(cli\)$"):
        picked(OnInvalid.USE_DEFAULT, "abc", "cli")


def test_a_bad_code_default_is_never_hidden():
    with pytest.raises(InputError):
        choose("x", [Candidate("abc", "default", explicit=False)], check_positive, OnInvalid.USE_DEFAULT)


def test_a_good_value_warns_nothing(caplog):
    assert picked(OnInvalid.USE_DEFAULT, 4).value == 4 and caplog.records == []


def test_an_unset_chain_is_none():
    assert choose("x", [Candidate(None, "cli")], check_positive, OnInvalid.ERROR) is None


def write(tmp_path, text):
    path = tmp_path / "c.yaml"
    path.write_text(text)
    return path


@pytest.mark.parametrize("key, text, value", [
    (table.GROUPING_TURNS, "device: {grouping: {turns: abc}}\n", 3),
    (table.GROUPING_SESSIONS, "device: {grouping: {sessions: 0}}\n", 2),
    (table.GROUPING_LIMIT, "device: {grouping: {limit: -1}}\n", None),
    (table.APPS_LIMIT, "apps: {limit: x}\n", None),
    (table.GROUPING_NO_RERUN, "device: {grouping: {noRerun: maybe}}\n", True),
    (table.APPS_MEASURE, "apps: {measure: 'yes'}\n", False),
    (table.SCREENING_AI_REVIEW, "device: {screening: {aiReview: 'yes'}}\n", False),
    (table.PATHS_RESULTS, "paths: {results: 3}\n", None),
    (table.PATHS_PROMPTS, "paths: {prompts: ''}\n", None),
    (table.BENCHMARK_CONFIG, "device: {benchmark: {config: []}}\n", None),
])
def test_a_bad_file_value_warns_once_and_reads_the_default(tmp_path, caplog, key, text, value):
    loaded = load(write(tmp_path, text), {}, {})
    assert loaded.read(key) == value and loaded.read(key) == value
    # a command's logger passes DEBUG on to events.jsonl; the warning is the one line at INFO or above
    shown = [r.getMessage() for r in caplog.records if r.levelno >= logging.INFO]
    assert len(shown) == 1 and shown[0].startswith(f"invalid: {key.key} ")
    assert loaded.sources[key.key] == "default"


def test_a_bad_mode_in_the_file_warns_and_a_bad_flag_is_argparse(tmp_path, capsys):
    config = write(tmp_path, "apps: {mode: fast}\n")
    code = guide(["--app", str(tmp_path), "--device-results", str(tmp_path), "--agent", "dry-run",
                  "--perfrepair-config", str(config)])
    err = capsys.readouterr().err
    assert code == 1 and "invalid: apps.mode fast, one of ['battery', 'latency']; using the default latency" in err
    with pytest.raises(SystemExit) as e:
        guide(["--app", "a", "--mode", "fast"])
    assert e.value.code == 2


def test_a_catalog_that_is_no_path_stops_the_step(tmp_path, capsys):
    config = write(tmp_path, "device: {screening: {catalog: 3}}\n")
    assert grouping(["build", "--device-results", str(tmp_path), "--perfrepair-config", str(config)]) == 1
    assert capsys.readouterr().err.splitlines()[-1] == f"error invalid: device.screening.catalog 3, a path (file {config})"


def test_a_malformed_setting_warns_and_the_command_proceeds(tmp_path, capsys):
    config = write(tmp_path, "paths: {results: r}\ndevice: {grouping: {turns: abc}}\n")
    assert grouping(["assign", "--device-results", str(tmp_path), "--agent", "dry-run", "--perfrepair-config", str(config)]) == 1
    err = capsys.readouterr().err
    assert f"invalid: device.grouping.turns abc, a positive integer; using the default 3 (file {config})" in err
    assert "error " in err.splitlines()[-1] and "invalid" not in err.splitlines()[-1]
