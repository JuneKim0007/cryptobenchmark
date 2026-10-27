"""A scope re-found in today's source: its function's offsets and the one call `scope.call` names on `scope.line`."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ...dto.site import Scope
from .calls import Arguments, arguments
from .lexer import Source, lex
from .reject import Rejected


@dataclass(frozen=True)
class Located:
    function: tuple[int, int]
    call: int
    args: Arguments


def line_offsets(text: str) -> list[int]:
    return [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]


def function_span(source: Source, scope: Scope) -> tuple[int, int]:
    """Offsets from the start of line `scope.start` to the end of line `scope.end`; its braces must balance."""
    starts = line_offsets(source.text)
    if not 1 <= scope.start <= scope.line <= scope.end <= len(starts):
        raise Rejected("call_moved")
    end = starts[scope.end] if scope.end < len(starts) else len(source.text)
    masked, depth = source.masked[starts[scope.start - 1]:end], 0
    for ch in masked:
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth < 0:
            raise Rejected("function_span")
    if depth:
        raise Rejected("function_span")
    return starts[scope.start - 1], end


def _head(call: str) -> re.Pattern:
    masked = lex(call).masked
    if "(" not in masked:
        raise Rejected("unsupported_expression")
    parts = [p.strip() for p in masked[:masked.index("(")].split(".")]
    if not all(re.fullmatch(r"\w+", p) for p in parts):
        raise Rejected("unsupported_expression")
    return re.compile(r"\b" + r"\s*\.\s*".join(map(re.escape, parts)) + r"\s*\(")


def locate(source: Source, scope: Scope) -> Located:
    function = function_span(source, scope)
    starts, masked = line_offsets(source.text), source.masked
    want = lex(scope.call).normalized(0, len(scope.call))
    line_start = starts[scope.line - 1]
    line_end = starts[scope.line] if scope.line < len(starts) else len(source.text)
    found = []
    for m in _head(scope.call).finditer(masked, line_start, line_end):
        args = arguments(masked, m.end() - 1)
        if args.close < function[1] and source.normalized(m.start(), args.close + 1) == want:
            found.append(Located(function, m.start(), args))
    if not found:
        raise Rejected("call_moved")
    if len(found) > 1:
        raise Rejected("ambiguous_call")
    return found[0]
