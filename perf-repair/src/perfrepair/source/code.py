"""Code: a source text with its masked copy and classes; lines, normalized spellings, literals, arguments, expression end."""
from __future__ import annotations

import bisect
from dataclasses import dataclass, field

from .brackets import CLOSE, OPEN, matching, split_spans
from .language import Language
from .lexer import CODE, LITERAL, STRING, lex, line_starts


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
        masked, classes = lex(text, language, True)
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
                and STRING.fullmatch(self.text, start, end) is not None)

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
