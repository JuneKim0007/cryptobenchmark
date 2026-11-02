"""Same-file string constants folded to their value: `const val`, top-level or object `val`, `static final String`."""
from __future__ import annotations

import re
from collections import Counter

from ..source.language import JAVA, KOTLIN
from ..source.lexer import Code, literal, opening, split_top

_KOTLIN = re.compile(r"\b(const\s+)?val\s+(\w+)\s*(?::\s*String\s*)?=")
_JAVA = re.compile(r"\b((?:(?:public|private|protected|static|final)\s+)+)String\s+(\w+)\s*=")
_DECLARED = re.compile(r"\b(?:val|var)\s+(\w+)|\b[\w>\]]+\s+(\w+)\s*(?==[^=])")
_TYPE = re.compile(r"\b(?:class|object|interface|enum\s+class|enum)\s+(\w+)")
_OBJECT_HEADER = re.compile(r"\bobject\b[^;{}]*$")
_NAME = re.compile(r"(?:(\w+)\s*\.\s*)?(\w+)")
_CONTINUED = ("+",)


def _enclosing_brace(masked: str, offset: int) -> int | None:
    depth = 0
    for k in range(offset - 1, -1, -1):
        ch = masked[k]
        if ch == "}":
            depth += 1
        elif ch == "{":
            if depth == 0:
                return k
            depth -= 1
    return None


def _member_level(code: Code, offset: int) -> bool:
    """Kotlin: at top level or directly in an object body."""
    brace = _enclosing_brace(code.masked, offset)
    if brace is None:
        return True
    return bool(_OBJECT_HEADER.search(code.masked[max(0, brace - 200):brace]))


def _kotlin(code: Code):
    return (d for d in _KOTLIN.finditer(code.masked) if d.group(1) or _member_level(code, d.start()))


def _java(code: Code):
    return (d for d in _JAVA.finditer(code.masked) if {"static", "final"} <= set(d.group(1).split()))


_DECLARATIONS = {KOTLIN: _kotlin, JAVA: _java}


def declarations(code: Code) -> dict[str, str]:
    """Constant name → initializer text, for names declared exactly once in the file."""
    found: dict[str, str] = {}
    m = code.masked
    for d in _DECLARATIONS[code.language](code):
        found[d.group(2)] = code.text[d.end():code.expression_end(d.end(), _CONTINUED, _CONTINUED)].strip()
    counts = Counter(a or b for a, b in _DECLARED.findall(m))
    return {k: v for k, v in found.items() if counts[k] <= 1}


class Constants:
    def __init__(self, code: Code):
        self.code = code
        self.table = declarations(code)
        self.types = set(_TYPE.findall(code.masked)) | {"Companion"}

    def fold(self, expr: str, seen: frozenset[str] = frozenset()) -> str | None:
        """The string value of a literal, a constant, or a '+' of those; None when any part is not one."""
        value = literal(expr, self.code.language)
        if value is not None:
            return value
        sub = Code.of(expr, self.code.language)
        parts = split_top(sub.masked, sub.text, 0, len(sub.text), "+")
        if len(parts) > 1:
            values = [self.fold(p, seen) for p in parts]
            return None if None in values else "".join(values)
        stripped = expr.strip()
        if stripped.startswith("(") and stripped.endswith(")") and opening(stripped, len(stripped) - 1) == 0:
            return self.fold(stripped[1:-1], seen)
        m = _NAME.fullmatch(stripped)
        if not m or (m.group(1) and m.group(1) not in self.types):
            return None
        name = m.group(2)
        if name in seen or name not in self.table:
            return None
        return self.fold(self.table[name], seen | {name})
