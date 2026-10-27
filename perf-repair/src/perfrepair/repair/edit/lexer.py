"""Java and Kotlin source as code, literals and comments: a masked copy of the same length for searching code only."""
from __future__ import annotations

import re
from dataclasses import dataclass

CODE, LITERAL, COMMENT = "c", "s", "m"
LANGUAGES = {".java": "java", ".kt": "kotlin"}
_STRING = re.compile(r'"(?:[^"\\\n]|\\.)*"')


@dataclass(frozen=True)
class Source:
    text: str
    classes: str

    @property
    def masked(self) -> str:
        """Literal characters read '"' and comment characters ' '; newlines survive, offsets match `text`."""
        return "".join(ch if k == CODE or ch == "\n" else ('"' if k == LITERAL else " ")
                       for ch, k in zip(self.text, self.classes))

    def normalized(self, start: int, end: int) -> str:
        """Code without whitespace or comments, literals verbatim: two spellings of one call compare equal."""
        return "".join(ch for ch, k in zip(self.text[start:end], self.classes[start:end])
                       if k == LITERAL or (k == CODE and not ch.isspace()))

    def is_literal(self, start: int, end: int) -> bool:
        return (all(k == LITERAL for k in self.classes[start:end])
                and _STRING.fullmatch(self.text, start, end) is not None)


def _template_end(text: str, i: int) -> int:
    """End of a Kotlin `${...}` template inside a string, counting braces."""
    depth = 0
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return i


def lex(text: str) -> Source:
    classes, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end < 0 else end
            kind = COMMENT
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            kind = COMMENT
        elif text.startswith('"""', i):
            end = text.find('"""', i + 3)
            end = n if end < 0 else end + 3
            while end < n and text[end] == '"':
                end += 1
            kind = LITERAL
        elif text[i] in "\"'":
            end, quote = i + 1, text[i]
            while end < n and text[end] != quote and text[end] != "\n":
                if text[end] == "\\":
                    end += 2
                elif text.startswith("${", end):
                    end = _template_end(text, end + 1)
                else:
                    end += 1
            end = min(end + 1, n)
            kind = LITERAL
        else:
            end, kind = i + 1, CODE
        classes.append(kind * (end - i))
        i = end
    return Source(text, "".join(classes))
