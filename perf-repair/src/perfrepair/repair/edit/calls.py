"""A call's argument list read from masked source: the closing parenthesis and each top-level argument's span."""
from __future__ import annotations

from dataclasses import dataclass

from .reject import Rejected

_OPEN, _CLOSE = "([{", ")]}"


@dataclass(frozen=True)
class Arguments:
    open: int
    close: int
    spans: tuple[tuple[int, int], ...]


def _trimmed(masked: str, start: int, end: int) -> tuple[int, int]:
    while start < end and masked[start].isspace():
        start += 1
    while end > start and masked[end - 1].isspace():
        end -= 1
    return start, end


def arguments(masked: str, open_: int) -> Arguments:
    """`open_` indexes the '('; generic angle brackets are not counted, so `f(Map<A, B>)` splits in two."""
    depth, start, spans = 0, open_ + 1, []
    for i in range(open_ + 1, len(masked)):
        ch = masked[i]
        if ch in _OPEN:
            depth += 1
        elif ch in _CLOSE:
            if depth == 0:
                last = _trimmed(masked, start, i)
                if last[0] < last[1] or spans:
                    spans.append(last)
                return Arguments(open_, i, tuple(spans))
            depth -= 1
        elif ch == "," and depth == 0:
            spans.append(_trimmed(masked, start, i))
            start = i + 1
    raise Rejected("unbalanced_call")
