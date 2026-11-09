"""The checks a row or a gateway's settings class names: a set value that fails raises Invalid."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from ..dto.bundled import FROM_APPS
from ..dto.change import CHANGES
from ..dto.perf_mode import ALL, GENERIC, KEYS, PerfMode


class Invalid(ValueError):

    def __init__(self, name: str, value: Any, expected: str):
        super().__init__(name)
        self.name, self.value, self.expected = name, value, expected


def _check(name: str, value: Any, ok: bool, expected: str) -> None:
    if value is not None and not ok:
        raise Invalid(name, value, expected)


def check_any(_name: str, _value: Any) -> None:
    pass


def check_one_of(name: str, value: Any, choices: tuple[str, ...]) -> None:
    _check(name, value, value in choices, f"one of {list(choices)}")


def check_text(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, str) and value != "", "a non-empty string")


def check_positive(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, int) and not isinstance(value, bool) and value > 0, "a positive integer")


UNLIMITED = "unlimited"


def check_positive_or_unlimited(name: str, value: Any) -> None:
    if value != UNLIMITED:
        check_positive(name, value)


# a run id names runs/run_<id>.json: one path segment
RUN_ID_FORM = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def check_run_id(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, str) and bool(RUN_ID_FORM.fullmatch(value)),
           "letters, digits, '.', '_' or '-', not starting with a symbol")


def check_bool(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, bool), "true or false")


def _entry(entry: Any, key: str) -> str | None:
    if isinstance(entry, Mapping) and key in entry and set(entry) <= {key, "perfMode"}:
        entry = entry[key]
    elif key == "root":
        return None
    return entry if isinstance(entry, str) and entry else None


def target_path(entry: Any) -> str | None:
    """The path of one apps.targets path entry: a bare string, or a mapping of `path` and optionally `perfMode`."""
    return _entry(entry, "path")


def target_root(entry: Any) -> str | None:
    """The folder of one apps.targets root entry: a mapping of `root` and optionally `perfMode`."""
    return _entry(entry, "root")


def target_perf(entry: Any) -> PerfMode | None:
    """An apps.targets entry's own perfMode; None takes apps.perfMode. A bad one raises ValueError."""
    value = entry.get("perfMode") if isinstance(entry, Mapping) else None
    return None if value is None else PerfMode.parse(value)


def target_ok(entry: Any) -> bool:
    try:
        target_perf(entry)
        return bool(target_path(entry) or target_root(entry))
    except ValueError:
        return False


TARGETS_EXPECTED = "a list of paths, {path: ...} or {root: ...} each with an optional perfMode, or a targets file"


def check_targets(name: str, value: Any) -> None:
    listed = isinstance(value, list) and all(target_ok(e) for e in value)
    _check(name, value, listed or (isinstance(value, str) and value != ""), TARGETS_EXPECTED)


def check_path(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, Path) or (isinstance(value, str) and value != ""), "a path")


def check_from_apps(name: str, value: Any) -> None:
    # YAML 1.1 reads a bare `off` as false
    _check(name, value, value is False or value in FROM_APPS, f"one of {list(FROM_APPS)}")


def check_perf_mode(name: str, value: Any) -> None:
    try:
        ok = value is None or bool(PerfMode.parse(value))
    except ValueError:
        ok = False
    _check(name, value, ok, f"{GENERIC}, {ALL} or a list of {list(KEYS)}")


def check_max_change(name: str, value: Any) -> None:
    check_one_of(name, value, CHANGES)
