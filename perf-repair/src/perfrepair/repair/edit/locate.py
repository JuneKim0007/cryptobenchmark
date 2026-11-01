"""A scope re-found in today's source: its function's offsets and the one call `scope.call` names on `scope.line`."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ...app.lexer import Arguments, Code
from ...dto.site import Scope
from .reject import Rejected


@dataclass(frozen=True)
class Located:
    function: tuple[int, int]
    call: int
    args: Arguments


def call_arguments(code: Code, open_paren: int) -> Arguments:
    args = code.argument_spans(open_paren)
    if args is None:
        raise Rejected("unbalanced_call")
    return args


def function_span(code: Code, scope: Scope) -> tuple[int, int]:
    """Offsets from the start of line `scope.start` to the end of line `scope.end`; its braces must balance."""
    starts = code.starts
    if not 1 <= scope.start <= scope.line <= scope.end <= len(starts):
        raise Rejected("call_moved")
    end = starts[scope.end] if scope.end < len(starts) else len(code.text)
    masked, depth = code.masked[starts[scope.start - 1]:end], 0
    for ch in masked:
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth < 0:
            raise Rejected("function_span")
    if depth:
        raise Rejected("function_span")
    return starts[scope.start - 1], end


def _head(call: Code) -> re.Pattern:
    masked = call.masked
    if "(" not in masked:
        raise Rejected("unsupported_expression")
    parts = [p.strip() for p in masked[:masked.index("(")].split(".")]
    if not all(re.fullmatch(r"\w+", p) for p in parts):
        raise Rejected("unsupported_expression")
    return re.compile(r"\b" + r"\s*\.\s*".join(map(re.escape, parts)) + r"\s*\(")


def locate(code: Code, scope: Scope) -> Located:
    """The call is lexed in the file's language, as the scope step lexed it."""
    function = function_span(code, scope)
    call = Code.of(scope.call, code.language)
    want = call.normalized(0, len(scope.call))
    line_start = code.starts[scope.line - 1]
    line_end = code.starts[scope.line] if scope.line < len(code.starts) else len(code.text)
    found = []
    for m in _head(call).finditer(code.masked, line_start, line_end):
        args = call_arguments(code, m.end() - 1)
        if args.close < function[1] and code.normalized(m.start(), args.close + 1) == want:
            found.append(Located(function, m.start(), args))
    if not found:
        raise Rejected("call_moved")
    if len(found) > 1:
        raise Rejected("ambiguous_call")
    return found[0]
