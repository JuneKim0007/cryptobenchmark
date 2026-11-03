"""A function's sinks and key source as views: patterns.yaml matched against its masked body; the key source from the
lifecycle's key requirement when it knows one."""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from ..dto.lifecycle import Lifecycle
from ..dto.site import KEY_SOURCES, SINKS
from ..files import read_yaml
from ..source.lexer import Code
from .extract import Function

PATTERNS = Path(__file__).with_name("patterns.yaml")
SUPPORTED_SCHEMA = 1


@dataclass(frozen=True)
class Patterns:
    sinks: dict[str, tuple[re.Pattern, ...]]
    keySources: dict[str, tuple[re.Pattern, ...]]
    keyCalls: re.Pattern
    fieldWrite: re.Pattern


@cache
def read_patterns(path: Path = PATTERNS) -> Patterns:
    doc = read_yaml(path)
    if doc.get("schemaVersion") != SUPPORTED_SCHEMA:
        raise ValueError(f"{path}: schemaVersion {doc.get('schemaVersion')} is not {SUPPORTED_SCHEMA}")
    unknown = (set(doc["sinks"]) - set(SINKS)) | (set(doc["keySources"]) - set(KEY_SOURCES))
    if unknown:
        raise ValueError(f"{path}: kinds {sorted(unknown)} are not in the Scope contract")
    compile_all = lambda d: {k: tuple(re.compile(p) for p in v) for k, v in d.items()}
    return Patterns(compile_all(doc["sinks"]), compile_all(doc["keySources"]), re.compile(doc["keyCalls"]),
                    re.compile(doc["fieldWrite"]))


def sinks(code: Code, fn: Function, patterns: Patterns) -> tuple[str, ...]:
    body = code.masked[fn.start:fn.end]
    found = {kind for kind, ps in patterns.sinks.items() if any(p.search(body) for p in ps)}
    if fn.expression:
        found.add("return")
    if found:
        return tuple(s for s in SINKS if s in found)
    return ("unknown",) if patterns.fieldWrite.search(body) else ("local",)


def key_source(code: Code, fn: Function, patterns: Patterns) -> str:
    body = code.masked[fn.start:fn.end]
    for kind in KEY_SOURCES:
        if any(p.search(body) for p in patterns.keySources.get(kind, ())):
            return kind
    params = set(fn.params)
    for m in patterns.keyCalls.finditer(code.masked, fn.start, fn.end):
        parsed = code.arguments(m.end() - 1)
        if parsed and params & {a.strip() for a in parsed[0]}:
            return "parameter"
    return "unknown"


def settled_key_source(lifecycle: Lifecycle, current: str) -> str:
    """A settled key origin fills only a view code left open; a closed reading stays."""
    key = lifecycle.origin_of("key")
    done = key.settled if key is not None else None
    if done is None or done.origin not in KEY_SOURCES or current not in ("unknown", "parameter"):
        return current
    return done.origin


def key_source_view(lifecycle: Lifecycle | None, regex: str) -> str:
    """The key requirement's origin when the lifecycle knows it, one method away for a field or private parameter;
    else the pattern reading."""
    key = lifecycle.origin_of("key") if lifecycle is not None else None
    if key is None:
        return regex
    depth1 = key.depth1[0] if len(key.depth1) == 1 else None
    for candidate in (key.origin, depth1):
        if candidate in KEY_SOURCES and candidate != "unknown" and not (candidate == "parameter" and depth1):
            return candidate
    return regex
