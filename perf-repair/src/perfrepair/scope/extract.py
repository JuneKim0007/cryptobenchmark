"""Named functions of a Java or Kotlin file with their spans, by bracket matching over comment- and string-masked text.

Lambdas, anonymous objects and local blocks are transparent: a call belongs to the innermost named function around it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..source.brackets import matching, opening, split_top
from ..source.code import Code
from ..source.language import JAVA, KOTLIN

JAVA_KEYWORDS = frozenset({"if", "for", "while", "switch", "catch", "synchronized", "try", "else", "do", "return",
                           "new", "super", "this", "assert", "throw", "when", "case", "finally"})
NOT_DECLARATION = frozenset({"new", "record", "->", "return"})
KOTLIN_MODIFIERS = ("private", "public", "protected", "internal", "override", "open", "final", "abstract", "suspend",
                    "inline", "operator", "infix", "tailrec", "external", "actual", "expect", "static")
KOTLIN_PARAM_MODIFIERS = frozenset({"vararg", "val", "var", "noinline", "crossinline"})

_JAVA_HEAD = re.compile(r"\)\s*(?:throws\s+[\w.\s,<>]+?)?\s*$")
_NAME_BEFORE = re.compile(r"(\w+)\s*$")
_TOKEN_BEFORE = re.compile(r"(\S+)\s*$")
_KOTLIN_FUN = re.compile(r"\bfun\b")
_KOTLIN_CTOR = re.compile(r"\bconstructor\s*\(")
_KOTLIN_PREFIX = re.compile(r"(?:(?:@[\w.:]+(?:\([^()]*\))?|" + "|".join(KOTLIN_MODIFIERS) + r")\s+)+$")
_KOTLIN_STOP = re.compile(r"\b(?:fun|val|var|class|object|interface)\b|[{};@]")
_PRIMARY = re.compile(r"\bclass\s+\w+[^{};]*$")
_CONTINUES_AFTER = ("=", "+", "-", "*", "/", "%", "&&", "||", ".", ",", "(", "?:", "->", "?", ":")
_CONTINUES_BEFORE = (".", "?.", "?:", "&&", "||", "+", "*", "/", "->", ")")


@dataclass(frozen=True)
class Function:
    name: str
    start: int
    end: int
    params: tuple[str, ...]
    expression: bool

    def contains(self, offset: int) -> bool:
        return self.start <= offset < self.end


def _java_params(code: Code, a: int, b: int) -> tuple[str, ...]:
    out = []
    for p in split_top(code.masked, code.masked, a, b, ","):
        m = _NAME_BEFORE.search(p.replace("...", " "))
        if m:
            out.append(m.group(1))
    return tuple(out)


def _kotlin_params(code: Code, a: int, b: int) -> tuple[str, ...]:
    out = []
    for p in split_top(code.masked, code.masked, a, b, ","):
        head = re.sub(r"@[\w.:]+(?:\([^()]*\))?", " ", p.split(":", 1)[0]).split()
        words = [w for w in head if w not in KOTLIN_PARAM_MODIFIERS]
        if words:
            out.append(words[-1])
    return tuple(out)


def _statement_start(masked: str, offset: int) -> int:
    k = max(masked.rfind(";", 0, offset), masked.rfind("{", 0, offset), masked.rfind("}", 0, offset)) + 1
    while k < offset and masked[k].isspace():
        k += 1
    return k


def _java(code: Code) -> list[Function]:
    m, out = code.masked, []
    for brace in (i for i, ch in enumerate(m) if ch == "{"):
        head = _JAVA_HEAD.search(m[max(0, brace - 400):brace])
        if not head:
            continue
        close = max(0, brace - 400) + head.start()
        open_ = opening(m, close)
        if open_ is None:
            continue
        w = max(0, open_ - 200)
        name = _NAME_BEFORE.search(m[w:open_])
        if not name or name.group(1) in JAVA_KEYWORDS or name.group(1)[0].isdigit():
            continue
        name_at = w + name.start(1)
        prior = _TOKEN_BEFORE.search(m[max(0, name_at - 100):name_at])
        if prior and (prior.group(1) in NOT_DECLARATION or prior.group(1)[-1] in ".=(,!&|?:+-*/<"):
            continue
        end = matching(m, brace)
        if end is None:
            continue
        out.append(Function(name.group(1), _statement_start(m, name_at), end + 1,
                            _java_params(code, open_ + 1, close), False))
    return out


def _kotlin_start(m: str, keyword: int) -> int:
    prefix = _KOTLIN_PREFIX.search(m[max(0, keyword - 300):keyword])
    return max(0, keyword - 300) + prefix.start() if prefix else keyword


def _kotlin_body(code: Code, close: int) -> tuple[int, int, bool] | None:
    """(start of body, end, expression?) after a parameter list's ')', or None for a function with no body."""
    m, k, depth = code.masked, close + 1, 0
    while k < len(m):
        ch = m[k]
        if ch in "(<":
            depth += 1
        elif ch in ")>" and depth and m[k - 1] != "-":
            depth -= 1
        elif depth == 0 and ch == "{":
            end = matching(m, k)
            return (k, end + 1, False) if end is not None else None
        elif depth == 0 and ch == "=" and m[k + 1:k + 2] != "=":
            return k, code.expression_end(k + 1, _CONTINUES_AFTER, _CONTINUES_BEFORE), True
        elif depth == 0 and _KOTLIN_STOP.match(m, k):
            return None
        k += 1
    return None


def _kotlin(code: Code) -> list[Function]:
    m, out = code.masked, []
    heads = [(f.start(), f.end()) for f in _KOTLIN_FUN.finditer(m)] + \
            [(c.start(), c.end() - 1) for c in _KOTLIN_CTOR.finditer(m)]
    for keyword, after in sorted(heads):
        paren = m.find("(", after)
        if paren < 0:
            continue
        header, start = m[after:paren], _kotlin_start(m, keyword)
        if header.strip() and _KOTLIN_STOP.search(header):
            continue
        if m.startswith("fun", keyword):
            found = _NAME_BEFORE.search(header)
            name = found.group(1) if found else None
        else:
            name = None if _PRIMARY.search(m[max(0, start - 300):start]) else "constructor"
        close = matching(m, paren)
        if name is None or close is None:
            continue
        body = _kotlin_body(code, close)
        if body is None:
            continue
        out.append(Function(name, start, body[1], _kotlin_params(code, paren + 1, close), body[2]))
    return out


_EXTRACTORS = {JAVA: _java, KOTLIN: _kotlin}


def functions(code: Code) -> list[Function]:
    return sorted(_EXTRACTORS[code.language](code), key=lambda f: (f.start, -f.end))


def enclosing(fns: list[Function], offset: int) -> Function | None:
    inside = [f for f in fns if f.contains(offset)]
    return min(inside, key=lambda f: f.end - f.start) if inside else None
