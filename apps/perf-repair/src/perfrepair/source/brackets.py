"""Bracket walking over masked text: the matching and opening bracket, top-level spans split on a separator."""
from __future__ import annotations

OPEN, CLOSE = "([{", ")]}"


def matching(masked: str, i: int) -> int | None:
    """Offset of the bracket closing the one at i, in masked text."""
    depth = 0
    for k in range(i, len(masked)):
        ch = masked[k]
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
            if depth == 0:
                return k
    return None


def opening(masked: str, i: int) -> int | None:
    """Offset of the bracket opening the one closing at i, in masked text."""
    depth = 0
    for k in range(i, -1, -1):
        ch = masked[k]
        if ch in CLOSE:
            depth += 1
        elif ch in OPEN:
            depth -= 1
            if depth == 0:
                return k
    return None


def _stripped(masked: str, a: int, b: int) -> tuple[int, int]:
    while a < b and masked[a].isspace():
        a += 1
    while b > a and masked[b - 1].isspace():
        b -= 1
    return a, b


def split_spans(masked: str, a: int, b: int, sep: str) -> list[tuple[int, int]]:
    """Spans of [a:b] split on `sep` outside brackets, trimmed of whitespace and comments via the masked copy."""
    spans, depth, start = [], 0, a
    for k in range(a, b):
        ch = masked[k]
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
        elif ch == sep and depth == 0:
            spans.append(_stripped(masked, start, k))
            start = k + 1
    spans.append(_stripped(masked, start, b))
    return spans


def split_top(masked: str, text: str, a: int, b: int, sep: str) -> list[str]:
    return [text[s:e] for s, e in split_spans(masked, a, b, sep)]
