"""stop/: the code table against every raise site and the docs; terminate's actions and the stops.<code> resolution."""
import ast
import logging
import re
from pathlib import Path

import pytest

from perfrepair.config.load import load
from perfrepair.config.stops import install_stops
from perfrepair.dto.event import FINDING
from perfrepair.inputs.table import STOP_ROWS
from perfrepair.log.status import status_line
from perfrepair.stop import CODES, STOP, WARN, Halt, terminate
from perfrepair.stop.codes import CODES_LIST, OVERRIDABLE
from helpers import captured_events

SRC = Path(__file__).parents[1] / "src" / "perfrepair"
CODED = re.compile(r"^([a-z][a-z0-9]*(?:_[a-z0-9]+)+|[a-z]+)(?::|$)")
# reasons a single edit is rejected for, recorded in edits.json; never a command's stop
EXEMPT = {"Rejected", "ArgumentTypeError"}
ANY = "[a-z0-9_]+"


def _first(node: ast.Call) -> ast.expr | None:
    return node.args[0] if node.args else None


def _pattern(arg: ast.expr | None) -> str | None:
    """A literal's code, or an f-string's code with `{...}` as any word: `{s}_failed` → `[a-z0-9_]+_failed`; one word
    is a code only as the whole literal (`InputError("invalid", ...)`), since `families: ...` is prose."""
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        found = CODED.match(arg.value)
        whole = found and (("_" in found.group(1)) or found.group(1) == arg.value)
        return re.escape(found.group(1)) if whole else None
    if isinstance(arg, ast.JoinedStr):
        text = "".join(re.escape(v.value) if isinstance(v, ast.Constant) else ANY for v in arg.values)
        found = re.match(r"^((?:\[a-z0-9_\]\+|[a-z0-9_])+)(?::|$|\\ )", text)
        code = found.group(1) if found else ""
        return code if "_" in code.replace(ANY, "") else None
    return None


def raised_codes() -> dict[str, list[str]]:
    """Per code pattern, its sites: terminate's first argument, and every raise whose message starts with a code."""
    found: dict[str, list[str]] = {}
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            call = node.exc if isinstance(node, ast.Raise) else node if isinstance(node, ast.Call) else None
            if not isinstance(call, ast.Call):
                continue
            name = getattr(call.func, "id", getattr(call.func, "attr", ""))
            if isinstance(node, ast.Call) and name != "terminate" or name in EXEMPT:
                continue
            pattern = _pattern(_first(call))
            if pattern:
                found.setdefault(pattern, []).append(f"{path.relative_to(SRC)}:{node.lineno}")
    return found


def test_every_code_raised_anywhere_is_in_the_table():
    missing = {p: sites for p, sites in raised_codes().items() if not any(re.fullmatch(p, c) for c in CODES)}
    assert missing == {}


def test_a_raised_code_is_carried_by_its_exception_type_never_only_by_its_words():
    # TypeError is a programming error: outside FAILURES, so a bug with a traceback, never read for a code
    plain = {"ValueError", "RuntimeError", "OSError", "FileNotFoundError"}
    found = [f"{path.relative_to(SRC)}:{node.lineno}" for path in sorted(SRC.rglob("*.py"))
             for node in ast.walk(ast.parse(path.read_text()))
             if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)
             and getattr(node.exc.func, "id", "") in plain and _pattern(_first(node.exc))]
    assert found == []


def test_each_code_is_in_the_table_once_with_a_next_step():
    assert len(CODES) == len(CODES_LIST) and all(c.next and c.action in c.allowed or c.fixed for c in CODES_LIST)


def test_every_overridable_code_has_a_settings_row():
    assert set(STOP_ROWS) == {c.code for c in OVERRIDABLE}


def fire(code, **kw):
    return terminate(code, "d", stage="device", step="s", **kw)


def test_a_default_stop_is_one_event_then_a_halt_with_its_next_step():
    with captured_events() as events:
        with pytest.raises(Halt) as e:
            fire("perf_mode_unmeasured")
    [event] = events
    assert e.value.code == "perf_mode_unmeasured" and e.value.next_step == CODES["perf_mode_unmeasured"].next
    assert event.event == FINDING and event.outcome == STOP and event.data["code"] == "perf_mode_unmeasured"
    assert status_line(event).startswith("perf_mode_unmeasured ")


def test_a_default_warning_returns_and_says_so_in_its_line():
    with captured_events() as events:
        assert fire("not_on_device", item="P", app="a") == WARN
    assert status_line(events[0]).startswith("not_on_device ") and "warn" in status_line(events[0])


def settings(tmp_path, text):
    path = tmp_path / "perfrepair.yaml"
    path.write_text(text)
    install_stops(load(path, {}, {}))


def test_stops_warn_turns_an_overridable_stop_into_a_warning(tmp_path):
    settings(tmp_path, "stops: {perf_mode_unmeasured: warn}\n")
    assert fire("perf_mode_unmeasured") == WARN


def test_a_fixed_code_ignores_the_setting_with_one_warning(tmp_path, caplog):
    settings(tmp_path, "stops: {charter_mismatch: warn}\n")
    for _ in range(2):
        with pytest.raises(Halt):
            fire("charter_mismatch")
    assert [r.getMessage().split(",")[0] for r in caplog.records if r.levelno == logging.WARNING] == [
        "stop_fixed: stops.charter_mismatch warn"]


def test_a_malformed_value_warns_and_takes_the_default(tmp_path, caplog):
    settings(tmp_path, "stops: {not_on_device: maybe}\n")
    assert fire("not_on_device") == WARN
    assert any(r.getMessage().startswith("invalid: stops.not_on_device") for r in caplog.records)


def test_an_action_the_code_does_not_allow_is_malformed(tmp_path):
    settings(tmp_path, "stops: {bundled_missing: skip}\n")
    assert fire("bundled_missing") == WARN
