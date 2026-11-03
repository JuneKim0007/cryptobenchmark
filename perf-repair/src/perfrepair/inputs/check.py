"""The checks a row or a gateway's settings class names: a set value that fails raises Invalid."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..dto.bundled import FROM_APPS
from ..dto.change import CHANGES
from ..dto.perf_mode import GENERIC, KEYS, PerfMode


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


def check_bool(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, bool), "true or false")


def target_path(entry: Any) -> str | None:
    """The path of one apps.targets entry: a bare string, or a mapping holding only `path`."""
    if isinstance(entry, Mapping) and set(entry) == {"path"}:
        entry = entry["path"]
    return entry if isinstance(entry, str) and entry else None


def check_targets(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, list) and all(target_path(e) for e in value), "a list of paths or {path: ...}")


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
    _check(name, value, ok, f"{GENERIC} or a list of {list(KEYS)}")


def check_max_change(name: str, value: Any) -> None:
    check_one_of(name, value, CHANGES)
