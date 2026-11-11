"""Halt: the one exception terminate raises."""
from __future__ import annotations


class Halt(Exception):
    """Raised only by terminate, after its event, so a catcher never writes a second line for it."""

    def __init__(self, code: str, detail: str, next_step: str, exit_code: int = 1, inner: str | None = None):
        self.code, self.detail, self.next_step, self.exit, self.inner = code, detail, next_step, exit_code, inner
        self.reported = True
        super().__init__(f"{code}: {detail}")
