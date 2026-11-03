"""The scope step: resolved sites → a Scope per site inside a named function, and the sites that have none."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..dto.lifecycle import Lifecycle
from ..dto.site import SCOPES_SCHEMA_VERSION, Scope, scope_id
from ..source.language import of_file
from ..source.lexer import Code
from .engines import read_engines
from .extract import enclosing, functions
from .facts import key_source, key_source_view, read_patterns, settled_key_source, sinks
from .lifecycle.read import Reading, read_site
from .lifecycle.settle import settle
from .syntax.parser import ParserMissing, parse

NO_FUNCTION, CALL_MOVED = "no_enclosing_function", "call_not_on_line"


@dataclass
class Scoping:
    scopes: list[Scope] = field(default_factory=list)
    unscoped: list[dict] = field(default_factory=list)
    lines: dict[str, int] = field(default_factory=dict)

    def statuses(self) -> dict[str, int]:
        return dict(sorted(Counter(s.lifecycle.status for s in self.scopes if s.lifecycle is not None).items()))

    def document(self, app: str) -> dict:
        return {"schemaVersion": SCOPES_SCHEMA_VERSION, "app": app, "scopes": [s.to_json() for s in self.scopes],
                "unscoped": self.unscoped}


def _offset(code: Code, line: int, call: str) -> int | None:
    at = code.text.find(call, code.starts[line - 1]) if 1 <= line <= len(code.starts) else -1
    return at if at >= 0 and code.line(at) == line else None


def _language(file: str):
    language = of_file(file)
    if language is None:
        raise ValueError(f"{file}: not a source language")
    return language


class _Trees:
    """One syntax tree per file; a missing parser is recorded once and every lifecycle says so."""

    def __init__(self):
        self.trees, self.missing = {}, False

    def reading(self, file: str, code: Code, site: dict) -> Reading:
        if self.missing:
            return Reading(Lifecycle.unsupported("parser_missing"))
        if file not in self.trees:
            try:
                self.trees[file] = parse(code.text, code.language)
            except ParserMissing:
                self.missing = True
                return Reading(Lifecycle.unsupported("parser_missing"))
        return read_site(self.trees[file], site, read_engines())


def build_scopes(app: str, root: Path, sites: list[dict]) -> Scoping:
    out, patterns, parsed, trees = Scoping(), read_patterns(), {}, _Trees()
    for s in sorted(sites, key=lambda s: (s["file"], s["line"], s["call"])):
        if s["file"] not in parsed:
            code = Code.of((Path(root) / s["file"]).read_text(errors="replace"), _language(s["file"]))
            parsed[s["file"]] = (code, functions(code))
            out.lines[s["file"]] = len(code.starts)
        code, fns = parsed[s["file"]]
        offset = _offset(code, s["line"], s["call"])
        fn = enclosing(fns, offset) if offset is not None else None
        if fn is None:
            out.unscoped.append({"file": s["file"], "line": s["line"], "call": s["call"],
                                 "reason": CALL_MOVED if offset is None else NO_FUNCTION})
            continue
        sid = scope_id(app, s["file"], fn.name, s["line"], s["call"])
        lifecycle = settle(trees.reading(s["file"], code, s), read_engines())
        out.scopes.append(Scope(
            id=sid, app=app, file=s["file"], line=s["line"],
            call=s["call"], function=fn.name, start=code.line(fn.start), end=code.line(fn.end - 1),
            engineType=s["engineType"], algorithm=s["resolvedAlgorithm"], provider=s["resolvedProvider"],
            resolution=s["resolution"], sinks=sinks(code, fn, patterns),
            keySource=settled_key_source(lifecycle, key_source_view(lifecycle, key_source(code, fn, patterns))),
            lifecycle=lifecycle))
    return out
