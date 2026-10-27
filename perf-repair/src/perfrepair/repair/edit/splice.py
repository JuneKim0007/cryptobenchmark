"""Exact-span text replacement that keeps every line number, and its unified diff."""
from __future__ import annotations

import difflib
from dataclasses import dataclass

from .reject import Rejected


@dataclass(frozen=True)
class Splice:
    start: int
    end: int
    text: str


def apply(text: str, splices: list[Splice]) -> str:
    """Newlines inside a replaced span follow the new text, so a scope's lines `start..end` stay put in the copy."""
    out, last = [], 0
    for s in sorted(splices, key=lambda s: (s.start, s.end)):
        if s.start < last:
            raise Rejected("overlapping_edits")
        lost = text.count("\n", s.start, s.end) - s.text.count("\n")
        if lost < 0:
            raise ValueError(f"splice at {s.start} adds lines")
        out += [text[last:s.start], s.text, "\n" * lost]
        last = s.end
    return "".join(out + [text[last:]])


def diff(file: str, before: str, after: str) -> str:
    return "".join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                        f"a/{file}", f"b/{file}"))
