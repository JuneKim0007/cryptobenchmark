"""The installed reader of `stops.<code>`: the first command of a run that loads settings installs it; without one, or
for a code it leaves unset, the code's default stands."""
from __future__ import annotations

from typing import Callable, Optional

from ..log.attach import current_run
from .codes import Code

Reader = Callable[[Code], Optional[str]]
_reader: Reader | None = None
_run: str | None = None


def install(reader: Reader) -> None:
    # a command another one calls in-process joins its caller's run and keeps its caller's settings
    global _reader, _run
    if _reader is not None and _run is not None and _run == current_run():
        return
    _reader, _run = reader, current_run()


def reset() -> None:
    global _reader, _run
    _reader, _run = None, None


def action(code: Code) -> str:
    """A fixed code's reader only warns that it was set."""
    chosen = _reader(code) if _reader is not None else None
    return code.action if code.fixed or chosen is None else chosen
