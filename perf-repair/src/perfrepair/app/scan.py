"""`<EngineType>.getInstance(...)` calls in one source file, outside comments and strings, across lines."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from ..source.language import Language
from ..source.lexer import Code, literal

_GET_PROVIDER = re.compile(r'getProvider\s*\((.*)\)\s*$', re.S)


@dataclass(frozen=True)
class Argument:
    expr: str
    literal: str | None
    folded: bool = False


@dataclass(frozen=True)
class Site:
    file: str
    line: int
    engineType: str
    algorithm: Argument
    provider: Argument | None
    snippet: str
    call: str
    origin: str
    offset: int

    def to_json(self) -> dict:
        d = asdict(self)
        del d["offset"]
        return d


def call_pattern(engine_types: set[str]) -> re.Pattern | None:
    if not engine_types:
        return None
    return re.compile(r"\b(" + "|".join(sorted(map(re.escape, engine_types))) + r")\s*\.\s*getInstance\s*\(")


def provider_inner(expr: str) -> str | None:
    """The argument of a `getProvider(...)` provider expression, or None."""
    m = _GET_PROVIDER.search(expr)
    return m.group(1).strip() if m else None


def argument(expr: str, language: Language, provider: bool = False) -> Argument:
    value = literal(expr, language)
    if value is None and provider and (inner := provider_inner(expr)) is not None:
        value = literal(inner, language)
    return Argument(expr, value)


def scan(code: Code, rel: str, origin: str, pattern: re.Pattern) -> list[Site]:
    sites = []
    for m in pattern.finditer(code.masked):
        parsed = code.arguments(m.end() - 1)
        if not parsed or not parsed[0]:
            continue
        args, close = parsed
        line = code.line(m.start())
        sites.append(Site(
            file=rel, line=line, engineType=m.group(1),
            algorithm=argument(args[0], code.language),
            provider=argument(args[1], code.language, provider=True) if len(args) > 1 else None,
            snippet=code.line_text(line).strip(), call=code.text[m.start():close + 1], origin=origin,
            offset=m.start()))
    return sites
