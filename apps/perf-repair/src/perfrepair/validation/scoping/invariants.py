"""Scoping invariants checked against the app's source: the cited call, the pattern's reading, an inverse link's sides."""
from __future__ import annotations

import re

from ...dto.pattern import CREATED_PER_CALL, HELD_IN_FIELD
from ...dto.site import Scope
from ...dto.unit import Unit
from ...scope.engines import Engine, read_engines
from ...scope.units.relations import read_relations
from ...source.code import Code
from ..finding import BLOCKING, UNDECIDED, Violation
from .source import Sources, body, calls_on, function_at, line_end, line_start, squeezed

_USES = ("use", "consume")
INVERSE = "inverse"


def _at(s: Scope, line: int) -> str:
    return f"{s.file}:{line}"


def _undecided(invariant: str, s: Scope, why: str) -> Violation:
    return Violation(invariant, UNDECIDED, f"scope {s.id}", (_at(s, s.line), why), "check it by hand; the source does not decide it")


def site_line_holds_call(s: Scope, code: Code) -> list[Violation]:
    """The cited line starts the recorded call, which may run on over the next lines."""
    call = squeezed(s.call)
    head = call.split("(", 1)[0]
    lines = s.call.count("\n")
    first = squeezed(code.line_text(s.line))
    window = squeezed(code.text[line_start(code, s.line):line_end(code, s.line + lines)])
    if head in first and call in window:
        return []
    return [Violation("site_line_holds_call", BLOCKING, f"scope {s.id}", (_at(s, s.line), f"line reads {code.line_text(s.line).strip()[:80]!r}"),
                      "rerun the app step; an edit at this line would change other code")]


def _uses(s: Scope) -> list:
    return [t for t in s.lifecycle.steps if t.role in _USES] if s.lifecycle else []


def _setup_in(code: Code, text: str, receiver: str, s: Scope, engine: Engine, init_per_call: bool = False) -> list[str]:
    factory = read_engines().factory
    found = [] if init_per_call else [f"{receiver}.{c}" for c in sorted(engine.configuration)
             if re.search(rf"\b{re.escape(receiver)}\s*\??\.\s*{re.escape(c)}\s*\(", text)]
    if re.search(rf"\b{re.escape(s.engineType)}\s*\.\s*{re.escape(factory)}\s*\(", text):
        found.append(f"{s.engineType}.{factory}")
    return found


def held_in_field_setup_once(s: Scope, code: Code, init_per_call: frozenset[tuple[str, str]] = frozenset()) -> list[Violation]:
    """held_in_field: no method that uses the held object creates it again, nor configures it again unless the item's
    fixed variant itself inits per call; init_per_call holds those items as (engine type, algorithm)."""
    if s.patternReason != HELD_IN_FIELD:
        return []
    engine = read_engines().engines.get(s.engineType)
    own = function_at(code, s.line)
    out = []
    for t in _uses(s):
        f = function_at(code, t.line)
        receivers = {c.receiver for c in calls_on(code, t.line, t.call)} - {None}
        if engine is None or f is None or len(receivers) != 1:
            out.append(_undecided("held_in_field_setup_once", s, f"{_at(s, t.line)}: no single receiver of {t.call} in a function"))
            continue
        if own is not None and f.start == own.start:
            continue
        found = _setup_in(code, body(code, f), receivers.pop(), s, engine, (s.engineType, s.algorithm) in init_per_call)
        if found:
            out.append(Violation("held_in_field_setup_once", BLOCKING, f"scope {s.id}",
                                 (_at(s, t.line), f"function {f.name} also calls {', '.join(found)}"),
                                 "the setup runs per call: the pattern is notFixed; fix the scoper's reading"))
    return out


def created_per_call_one_function(s: Scope, code: Code) -> list[Violation]:
    """created_per_call: each use line holds its call, and one of them is in the function that creates the object."""
    if s.patternReason != CREATED_PER_CALL:
        return []
    own = function_at(code, s.line)
    if own is None:
        return [_undecided("created_per_call_one_function", s, "no function around the site")]
    missing = [t for t in _uses(s) if not calls_on(code, t.line, t.call)]
    out = [Violation("created_per_call_one_function", BLOCKING, f"scope {s.id}", (_at(s, t.line), f"line holds no {t.call} call"),
                     "rerun the app step; the step lines do not match the source") for t in missing]
    if not any(own.contains(line_start(code, t.line)) for t in _uses(s)):
        out.append(Violation("created_per_call_one_function", BLOCKING, f"scope {s.id}",
                             (_at(s, s.line), f"no use inside {own.name}; uses at {sorted(t.line for t in _uses(s))}"),
                             "creation and use are in different functions: the pattern is not created_per_call"))
    return out


def _operation(code: Code, s: Scope, engine: Engine, line: int, call: str) -> set[str]:
    out = set()
    by_step = read_relations().steps.get(s.engineType, {})
    for c in calls_on(code, line, call):
        if call in engine.by_call:
            out.add(engine.by_call[call])
        if call in by_step:
            out.add(by_step[call])
        if engine.by_argument and engine.by_argument[0] == call:
            args = code.arguments(c.open_paren)
            index, values = engine.by_argument[1], engine.by_argument[2]
            if args and len(args[0]) > index:
                value = args[0][index].strip().rsplit(".", 1)[-1]
                out |= {values[value]} if value in values else set()
    return out


def operations(code: Code, s: Scope) -> set[str]:
    """The operations a scope's steps perform, read from their lines by engines.yaml and relations.yaml."""
    engine = read_engines().engines.get(s.engineType)
    if engine is None or s.lifecycle is None:
        return set()
    return set().union(*(_operation(code, s, engine, t.line, t.call) for t in s.lifecycle.steps))


def inverse_link_sides(unit: Unit, scopes: dict[str, Scope], sources: Sources) -> list[Violation]:
    out = []
    for link in (k for k in unit.links if k.kind == INVERSE):
        a, b = scopes.get(link.a), scopes.get(link.b)
        if a is None or b is None:
            continue
        codes = sources.code(a.file), sources.code(b.file)
        if None in codes:
            out.append(_undecided("inverse_link_sides", a, sources.why_not(a.file if codes[0] is None else b.file)))
            continue
        ops_a, ops_b = operations(codes[0], a), operations(codes[1], b)
        if not ops_a or not ops_b:
            out.append(_undecided("inverse_link_sides", a, f"operations not readable: {sorted(ops_a)} / {sorted(ops_b)}"))
            continue
        pairs = read_relations().inverses.items()
        if not any((p in ops_a and c in ops_b) or (p in ops_b and c in ops_a) for p, c in pairs):
            out.append(Violation("inverse_link_sides", BLOCKING, f"unit {unit.id}",
                                 (_at(a, a.line) + f" {sorted(ops_a)}", _at(b, b.line) + f" {sorted(ops_b)}"),
                                 "the sides are not inverse operations: drop the link, or fix the lifecycle that read them"))
    return out


SCOPE_RULES = (site_line_holds_call, created_per_call_one_function)


def scoping_invariants(scopes: list[Scope], units: list[Unit], sources: Sources,
                       init_per_call: frozenset[tuple[str, str]] = frozenset()) -> list[Violation]:
    out = []
    for s in scopes:
        code = sources.code(s.file)
        if code is None:
            out.append(_undecided("site_line_holds_call", s, sources.why_not(s.file)))
            continue
        out += [v for rule in SCOPE_RULES for v in rule(s, code)] + held_in_field_setup_once(s, code, init_per_call)
    by_id = {s.id: s for s in scopes}
    return out + [v for u in units for v in inverse_link_sides(u, by_id, sources)]
