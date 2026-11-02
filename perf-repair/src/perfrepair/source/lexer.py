"""Java and Kotlin text classed as code, literal or comment; a masked copy at the same offsets; literals, arguments."""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

from .language import Language

OPEN, CLOSE = "([{", ")]}"
CODE, LITERAL, COMMENT = "c", "s", "m"

_STRING = re.compile(r'"((?:[^"\\\n]|\\.)*)"', re.S)
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


def _lex(text: str, language: Language, strings: bool) -> tuple[str, str]:
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
    return _lex(text, language, strings)[0]


def line_starts(text: str) -> tuple[int, ...]:
    return (0, *(m.end() for m in re.finditer("\n", text)))


def literal(expr: str, language: Language) -> str | None:
    """The value of a single string literal, or None; a string with a template is not a literal."""
    expr = expr.strip()
    m = _RAW.fullmatch(expr) or _STRING.fullmatch(expr)
    if not m or (language.template and re.search(r"(?<!\\)" + re.escape(language.template) + r"[\w{]", m.group(1))):
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


@dataclass(frozen=True)
class Arguments:
    open: int
    close: int
    spans: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class Code:
    text: str
    language: Language
    masked: str = field(repr=False)
    classes: str = field(repr=False)
    starts: tuple[int, ...] = field(repr=False)

    @classmethod
    def of(cls, text: str, language: Language) -> "Code":
        masked, classes = _lex(text, language, True)
        return cls(text, language, masked, classes, line_starts(text))

    def line(self, offset: int) -> int:
        return bisect.bisect_right(self.starts, offset)

    def line_text(self, line: int) -> str:
        return self.text.splitlines()[line - 1] if 1 <= line <= len(self.starts) else ""

    def normalized(self, start: int, end: int) -> str:
        """Code without whitespace or comments, literals verbatim: two spellings of one call compare equal."""
        return "".join(ch for ch, k in zip(self.text[start:end], self.classes[start:end])
                       if k == LITERAL or (k == CODE and not ch.isspace()))

    def is_literal(self, start: int, end: int) -> bool:
        """One double-quoted string literal, templates included."""
        return (start < end and all(k == LITERAL for k in self.classes[start:end])
                and _STRING.fullmatch(self.text, start, end) is not None)

    def argument_spans(self, open_paren: int) -> Arguments | None:
        """The call whose '(' is at open_paren: its ')' and each non-empty top-level argument's span."""
        close = matching(self.masked, open_paren)
        if close is None:
            return None
        spans = split_spans(self.masked, open_paren + 1, close, ",")
        return Arguments(open_paren, close, tuple((a, b) for a, b in spans if a < b))

    def arguments(self, open_paren: int) -> tuple[list[str], int] | None:
        """Top-level arguments of the call whose '(' is at open_paren, and the offset of its ')'."""
        args = self.argument_spans(open_paren)
        return None if args is None else ([self.text[a:b] for a, b in args.spans], args.close)

    def expression_end(self, start: int, continues_after: tuple[str, ...], continues_before: tuple[str, ...]) -> int:
        """End of the expression at start: ';', the enclosing close bracket, or a line end that no operator continues."""
        m, depth, k, last = self.masked, 0, start, start
        newline = self.language.newline_ends_statement
        while k < len(m):
            ch = m[k]
            if ch in OPEN:
                depth += 1
            elif ch in CLOSE:
                if depth == 0:
                    return last
                depth -= 1
            elif depth == 0 and ch == ";":
                return k
            elif depth == 0 and ch == "\n" and newline:
                before, after = m[start:k].rstrip(), m[k:].lstrip()
                if before and not before.endswith(continues_after) and not after.startswith(continues_before):
                    return last
            if not ch.isspace():
                last = k + 1
            k += 1
        return last
