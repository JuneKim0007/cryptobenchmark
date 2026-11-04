"""The reader of `stops.<code>` the settings layer installs; without one, or for a code it leaves unset, the code's
default stands."""
from __future__ import annotations

from typing import Callable, Optional

from .codes import Code

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
