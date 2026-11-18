"""The reader of `stops.<code>` the settings layer installs; without one, or for a code it leaves unset, the code's
default stands. An alias setting's value resolves through its code's glossary `values`."""
from __future__ import annotations

from typing import Callable, Optional

from .failures import CommandError
from .glossary import Code, codes

Reader = Callable[[Code], Optional[str]]
_reader: Reader | None = None


def install(reader: Reader) -> None:
    global _reader
    _reader = reader


def reset() -> None:
    global _reader
    _reader = None


def action(code: Code) -> str:
    """A fixed code's reader only warns that it was set."""
    chosen = _reader(code) if _reader is not None else None
    return code.action if code.fixed or chosen is None else chosen


def resolve(code: str, value: object, where: str) -> str:
    """The action an alias setting's value names for code, its glossary `values` the one vocabulary; any other value is refused."""
    values = codes()[code].get("values", {})
    if not isinstance(value, str) or value not in values:
        raise CommandError(f"invalid: {where} {value!r}, expected one of {list(values)}")
    return values[value]
