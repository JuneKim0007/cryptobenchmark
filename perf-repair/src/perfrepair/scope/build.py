"""The scope step: resolved sites → a Scope per site inside a named function, and the sites that have none."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..app.lexer import KOTLIN_SUFFIX, Code
from ..dto.site import SCHEMA_VERSION, Scope, scope_id
from .extract import enclosing, functions
from .facts import key_source, read_patterns, sinks

NO_FUNCTION, CALL_MOVED = "no_enclosing_function", "call_not_on_line"


@dataclass
class Scoping:
    scopes: list[Scope] = field(default_factory=list)
    unscoped: list[dict] = field(default_factory=list)

    def document(self, app: str) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "app": app, "scopes": [s.to_json() for s in self.scopes],
                "unscoped": self.unscoped}


def _offset(code: Code, line: int, call: str) -> int | None:
    at = code.text.find(call, code.starts[line - 1]) if 1 <= line <= len(code.starts) else -1
    return at if at >= 0 and code.line(at) == line else None


def build_scopes(app: str, root: Path, sites: list[dict]) -> Scoping:
    out, patterns, parsed = Scoping(), read_patterns(), {}
    for s in sorted(sites, key=lambda s: (s["file"], s["line"], s["call"])):
        if s["file"] not in parsed:
            code = Code.of((Path(root) / s["file"]).read_text(errors="replace"), s["file"].endswith(KOTLIN_SUFFIX))
            parsed[s["file"]] = (code, functions(code))
        code, fns = parsed[s["file"]]
        offset = _offset(code, s["line"], s["call"])
        fn = enclosing(fns, offset) if offset is not None else None
        if fn is None:
            out.unscoped.append({"file": s["file"], "line": s["line"], "call": s["call"],
                                 "reason": CALL_MOVED if offset is None else NO_FUNCTION})
            continue
        out.scopes.append(Scope(
            id=scope_id(app, s["file"], fn.name, s["line"], s["call"]), app=app, file=s["file"], line=s["line"],
            call=s["call"], function=fn.name, start=code.line(fn.start), end=code.line(fn.end - 1),
            engineType=s["engineType"], algorithm=s["resolvedAlgorithm"], provider=s["resolvedProvider"],
            resolution=s["resolution"], sinks=sinks(code, fn, patterns), keySource=key_source(code, fn, patterns)))
    return out
