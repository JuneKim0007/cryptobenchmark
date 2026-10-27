"""Java and Kotlin text with comments (and optionally string contents) blanked at the same offsets; literals, arguments."""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

KOTLIN_SUFFIX = ".kt"
OPEN, CLOSE = "([{", ")]}"

_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"', re.S)
_RAW = re.compile(r'"""(.*?)"""', re.S)
_TEMPLATE = re.compile(r'(?<!\\)\$[\w{]')


def _blank(out: list[str], a: int, b: int) -> None:
    for k in range(a, b):
        if out[k] != "\n":
            out[k] = " "


def _block_end(text: str, i: int, nested: bool) -> int:
    depth, k = 0, i
    while k < len(text):
        if text.startswith("/*", k) and (nested or depth == 0):
            depth, k = depth + 1, k + 2
        elif text.startswith("*/", k):
            depth, k = depth - 1, k + 2
            if depth == 0:
                return k
        else:
            k += 1
    return len(text)


def _quoted_end(text: str, i: int, quote: str, templates: bool) -> int:
    k = i + 1
    while k < len(text):
        ch = text[k]
        if ch == "\\":
            k += 2
        elif templates and text.startswith("${", k):
            depth, k = 1, k + 2
            while k < len(text) and depth:
                depth += {"{": 1, "}": -1}.get(text[k], 0)
                k += 1
        elif ch == quote:
            return k + 1
        elif ch == "\n":
            return k
        else:
            k += 1
    return len(text)


def mask(text: str, kotlin: bool, strings: bool = True) -> str:
    """Comments always, and string contents when `strings`, become spaces; newlines and quotes stay."""
    out, i, n = list(text), 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            _blank(out, i, j)
        elif text.startswith("/*", i):
            j = _block_end(text, i, kotlin)
            _blank(out, i, j)
        elif text.startswith('"""', i):
            j = text.find('"""', i + 3)
            j = n if j < 0 else j + 3
            while j < n and text[j] == '"':
                j += 1
            if strings:
                _blank(out, i + 3, max(i + 3, j - 3))
        elif text[i] in "\"'":
            j = _quoted_end(text, i, text[i], kotlin and text[i] == '"')
            if strings:
                _blank(out, i + 1, max(i + 1, j - 1))
        else:
            i += 1
            continue
        i = j
    return "".join(out)


def literal(expr: str, kotlin: bool) -> str | None:
    """The value of a single string literal, or None; a Kotlin template is not a literal."""
    expr = expr.strip()
    m = _RAW.fullmatch(expr) or _STRING.fullmatch(expr)
    if not m or (kotlin and _TEMPLATE.search(m.group(1))):
        return None
    return m.group(1)


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


def split_top(masked: str, text: str, a: int, b: int, sep: str) -> list[str]:
    """text[a:b] split on `sep` outside brackets, located through the masked copy."""
    parts, depth, start = [], 0, a
    for k in range(a, b):
        ch = masked[k]
        if ch in OPEN:
            depth += 1
        elif ch in CLOSE:
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append(text[start:k].strip())
            start = k + 1
    parts.append(text[start:b].strip())
    return parts


@dataclass(frozen=True)
class Code:
    text: str
    kotlin: bool
    masked: str = field(repr=False)
    starts: tuple[int, ...] = field(repr=False)

    @classmethod
    def of(cls, text: str, kotlin: bool) -> "Code":
        starts = (0, *(m.end() for m in re.finditer("\n", text)))
        return cls(text, kotlin, mask(text, kotlin), starts)

    def line(self, offset: int) -> int:
        return bisect.bisect_right(self.starts, offset)

    def line_text(self, line: int) -> str:
        return self.text.splitlines()[line - 1] if 1 <= line <= len(self.starts) else ""

    def arguments(self, open_paren: int) -> tuple[list[str], int] | None:
        """Top-level arguments of the call whose '(' is at open_paren, and the offset of its ')'."""
        close = matching(self.masked, open_paren)
        if close is None:
            return None
        args = split_top(self.masked, self.text, open_paren + 1, close, ",")
        return [a for a in args if a], close
