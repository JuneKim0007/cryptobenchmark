"""Halt: the one exception terminate raises; code_of: the code any failure carries, as a field or its message's first word."""
from __future__ import annotations

from ..log.status import CODE


class Halt(Exception):
    """Raised only by terminate, after its event, so a catcher never writes a second line for it."""

    def __init__(self, code: str, detail: str, next_step: str, exit_code: int = 1, inner: str | None = None):
        self.code, self.detail, self.next_step, self.exit, self.inner = code, detail, next_step, exit_code, inner
        self.reported = True
        super().__init__(f"{code}: {detail}")


def code_in(text: str) -> str | None:
    found = CODE.match((text or "").strip())
    return (found.group(1) or found.group(2)) if found else None


def code_of(e: BaseException) -> str | None:
    code = getattr(e, "code", None)
    return code if isinstance(code, str) else code_in(str(e))
