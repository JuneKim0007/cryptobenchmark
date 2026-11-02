"""The checks a row or a gateway's settings class names: a set value that fails raises Invalid."""
from __future__ import annotations

from pathlib import Path
from typing import Any


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


def check_path(name: str, value: Any) -> None:
    _check(name, value, isinstance(value, Path) or (isinstance(value, str) and value != ""), "a path")
