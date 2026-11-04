"""Same-file string constants folded to their value: `const val`, top-level or object `val`, `static final String`, each
under the type that declares it; a local assigned once in the site's function; Kotlin templates; SDK constants by table."""
from __future__ import annotations

import re
from collections import Counter

from ...catalog.sdk_constants import sdk_constants
from ...source.brackets import matching, opening, split_top
from ...source.code import Code
from ...source.language import JAVA, KOTLIN
from ...source.lexer import literal

_KOTLIN = re.compile(r"\b(const\s+)?val\s+(\w+)\s*(?::\s*String\s*)?=")
_JAVA = re.compile(r"\b((?:(?:public|private|protected|static|final)\s+)+)String\s+(\w+)\s*=")
_DECLARED = re.compile(r"\b(?:val|var)\s+(\w+)|\b[\w>\]]+\s+(\w+)\s*(?==[^=])")
_TYPE = re.compile(r"\b(?:class|object|interface|enum\s+class|enum)\s+(\w+)")
_TYPE_HEADER = re.compile(r"\b(?:class|object|interface|enum)\s+(\w+)[^;{}]*$|\bcompanion\s+object\b[^;{}]*$")
_OBJECT_HEADER = re.compile(r"\bobject\b[^;{}]*$")
_NAME = re.compile(r"(?:(\w+)\s*\.\s*)?(\w+)")
_TEMPLATE = re.compile(r"\$(?:\{(\w+)\}|(\w+))")
_STRING = re.compile(r'"((?:[^"\\$]|\\.|\$(?:\{\w+\}|\w+))*)"')
_CONTINUED = ("+",)
_HEADER = 200


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


def _type_of(masked: str, brace: int) -> str | None:
    """The type a brace opens the body of, or None; a companion object belongs to its class."""
    m = _TYPE_HEADER.search(masked[max(0, brace - _HEADER):brace])
    return None if m is None else (m.group(1) or "Companion")


def owner(masked: str, offset: int) -> str | None:
    """The innermost type declared around an offset, a companion object read as its class."""
    brace = _enclosing_brace(masked, offset)
    while brace is not None:
        found = _type_of(masked, brace)
        if found and found != "Companion":
            return found
        brace = _enclosing_brace(masked, brace)
    return None


def _member_level(code: Code, offset: int) -> bool:
    """Kotlin: at top level or directly in an object body."""
    brace = _enclosing_brace(code.masked, offset)
    if brace is None:
        return True
    return bool(_OBJECT_HEADER.search(code.masked[max(0, brace - _HEADER):brace]))


def _kotlin(code: Code):
    return (d for d in _KOTLIN.finditer(code.masked) if d.group(1) or _member_level(code, d.start()))


def _java(code: Code):
    return (d for d in _JAVA.finditer(code.masked) if {"static", "final"} <= set(d.group(1).split()))


_DECLARATIONS = {KOTLIN: _kotlin, JAVA: _java}


def declarations(code: Code) -> dict[str, list[tuple[str | None, str]]]:
    """Constant name → (declaring type, initializer text) for names no local declaration shadows."""
    found: dict[str, list[tuple[str | None, str]]] = {}
    for d in _DECLARATIONS[code.language](code):
        init = code.text[d.end():code.expression_end(d.end(), _CONTINUED, _CONTINUED)].strip()
        found.setdefault(d.group(2), []).append((owner(code.masked, d.start()), init))
    counts = Counter(a or b for a, b in _DECLARED.findall(code.masked))
    return {k: v for k, v in found.items() if counts[k] <= len(v)}


class Constants:
    def __init__(self, code: Code, sdk: dict[str, str] | None = None):
        self.code = code
        self.table = declarations(code)
        self.types = set(_TYPE.findall(code.masked)) | {"Companion"}
        self.sdk = sdk_constants() if sdk is None else sdk

    def _template(self, expr: str, seen: frozenset[str], at: int | None) -> str | None:
        m = _STRING.fullmatch(expr.strip()) if self.code.language.template else None
        if m is None:
            return None
        parts = [self.fold(t.group(1) or t.group(2), seen, at) for t in _TEMPLATE.finditer(m.group(1))]
        if None in parts:
            return None
        values = iter(parts)
        return _TEMPLATE.sub(lambda _: next(values), m.group(1))

    def _sdk(self, expr: str) -> str | None:
        flat = "".join(expr.split())
        return next((v for k, v in self.sdk.items() if flat == k or flat.endswith("." + k)), None)

    def _local(self, name: str, at: int) -> tuple[str, int] | None:
        """The initializer of a local assigned once before `at` in the site's function, never reassigned there."""
        brace, body = _enclosing_brace(self.code.masked, at), None
        while brace is not None and _type_of(self.code.masked, brace) is None:
            body, brace = brace, _enclosing_brace(self.code.masked, brace)
        if body is None:
            return None
        region = self.code.masked[body:matching(self.code.masked, body) or len(self.code.masked)]
        made = list(re.finditer(rf"\b(?:val|var|(?:final\s+)?String)\s+{name}\s*(?::\s*String\s*)?=(?!=)", region))
        assigned = re.findall(rf"(?<![\w.]){name}\s*=(?!=)", region)
        if len(made) != 1 or len(assigned) != 1 or body + made[0].end() > at:
            return None
        start = body + made[0].end()
        return self.code.text[start:self.code.expression_end(start, _CONTINUED, _CONTINUED)].strip(), start

    def _named(self, owner_name: str | None, name: str, seen: frozenset[str], at: int | None) -> str | None:
        local = self._local(name, at) if at is not None and owner_name is None else None
        if local is not None:
            return self.fold(local[0], seen | {name}, local[1])
        declared = self.table.get(name, [])
        if owner_name is not None and owner_name != "Companion":
            declared = [d for d in declared if d[0] == owner_name] or ([] if len(declared) > 1 else declared)
        elif len(declared) > 1 and at is not None:
            declared = [d for d in declared if d[0] == owner(self.code.masked, at)]
        return self.fold(declared[0][1], seen | {name}, None) if len(declared) == 1 else None

    def fold(self, expr: str, seen: frozenset[str] = frozenset(), at: int | None = None) -> str | None:
        """The string value of a literal, a constant, a template or a '+' of those; None when any part is not one.
        at: the site's offset, so a local of its function and its own type's constant can be read."""
        value = literal(expr, self.code.language)
        if value is not None:
            return value
        if (value := self._template(expr, seen, at)) is not None:
            return value
        sub = Code.of(expr, self.code.language)
        parts = split_top(sub.masked, sub.text, 0, len(sub.text), "+")
        if len(parts) > 1:
            values = [self.fold(p, seen, at) for p in parts]
            return None if None in values else "".join(values)
        stripped = expr.strip()
        if stripped.startswith("(") and stripped.endswith(")") and opening(stripped, len(stripped) - 1) == 0:
            return self.fold(stripped[1:-1], seen, at)
        if (value := self._sdk(stripped)) is not None:
            return value
        m = _NAME.fullmatch(stripped)
        if not m or (m.group(1) and m.group(1) not in self.types) or m.group(2) in seen:
            return None
        return self._named(m.group(1), m.group(2), seen, at)

