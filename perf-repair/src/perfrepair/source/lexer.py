"""Java and Kotlin text classed as code, literal or comment; a masked copy at the same offsets; literals."""
from __future__ import annotations

import re

from .language import Language

CODE, LITERAL, COMMENT = "c", "s", "m"

STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"', re.S)
_RAW = re.compile(r'"""(.*?)"""', re.S)


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


def _quoted_end(text: str, i: int, quote: str, template: str) -> int:
    k = i + 1
    while k < len(text):
        ch = text[k]
        if ch == "\\":
            k += 2
        elif template and text.startswith(template + "{", k):
            depth, k = 1, k + len(template) + 1
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


def _regions(text: str, language: Language):
    """(class, start, end, contents start, contents end) of every comment and literal, in order."""
    i, n = 0, len(text)
    while i < n:
        if text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            yield COMMENT, i, j, i, j
        elif text.startswith("/*", i):
            j = _block_end(text, i, language.nested_comments)
            yield COMMENT, i, j, i, j
        elif text.startswith('"""', i):
            j = text.find('"""', i + 3)
            j = n if j < 0 else j + 3
            while j < n and text[j] == '"':
                j += 1
            yield LITERAL, i, j, i + 3, max(i + 3, j - 3)
        elif text[i] in "\"'":
            j = _quoted_end(text, i, text[i], language.template if text[i] == '"' else "")
            yield LITERAL, i, j, i + 1, max(i + 1, j - 1)
        else:
            i += 1
            continue
        i = j


def lex(text: str, language: Language, strings: bool) -> tuple[str, str]:
    out, classes = list(text), [CODE] * len(text)
    for kind, a, b, inner_a, inner_b in _regions(text, language):
        classes[a:b] = [kind] * (b - a)
        if kind == COMMENT:
            _blank(out, a, b)
        elif strings:
            _blank(out, inner_a, inner_b)
    return "".join(out), "".join(classes)


def mask(text: str, language: Language, strings: bool = True) -> str:
    """Comments always, and string contents when `strings`, become spaces; newlines and quotes stay."""
    return lex(text, language, strings)[0]


def line_starts(text: str) -> tuple[int, ...]:
    return (0, *(m.end() for m in re.finditer("\n", text)))


def literal(expr: str, language: Language) -> str | None:
    """The value of a single string literal, or None; a string with a template is not a literal."""
    expr = expr.strip()
    m = _RAW.fullmatch(expr) or STRING.fullmatch(expr)
    if not m or (language.template and re.search(r"(?<!\\)" + re.escape(language.template) + r"[\w{]", m.group(1))):
        return None
    return m.group(1)
