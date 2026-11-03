"""One scope's gaps: each open requirement and a lost use with the lines code reached for it, the statements code
included, at most one other body; a requirement every reached line closes the same way is settled here, never asked."""
from __future__ import annotations

from dataclasses import dataclass, field

from ...dto.gaps import (CANDIDATE_PREFIX, GAP_PREFIX, USE_GAP, Body, Candidate, Gap, ScopeGaps, Statement,
                         UNKNOWN_ORIGIN)
from ...dto.lifecycle import CODE_SOURCE, REQUIREMENTS, Completion, Requirement
from ..engines import Engines
from ..syntax.declarations import enclosing_method
from ..syntax.node import Node
from .candidates import Reached, reach
from .read import Reading
from .use_lines import use_lines

# per scope: gaps asked, lines of the other body, characters of a shown line; a capped gap is recorded with no lines
GAPS_PER_SCOPE, BODY_LINES, TEXT_CHARS = 6, 40, 200
_LOST_USE = "use_not_found"


@dataclass(frozen=True)
class Where:
    """The scope's site: its id, file, function, the file's lines."""
    scope: str
    file: str
    function: str
    line: int
    lines: list[str]

    def text(self, line: int) -> str:
        return self.lines[line - 1].strip()[:TEXT_CHARS] if 1 <= line <= len(self.lines) else ""


@dataclass
class Found:
    """gaps: None when the scope has none; settled: per requirement key, what code alone closed it to."""
    gaps: ScopeGaps | None = None
    settled: dict[tuple, Completion] = field(default_factory=dict)


def _order(r: Requirement) -> tuple:
    return REQUIREMENTS.index(r.name), r.at, r.line


def _gap(number: int, requirement: tuple, reached: Reached, first: int, where: Where) -> Gap:
    name, origin, line, at = requirement
    rows = {x.line: x for x in reversed(reached.lines)}
    candidates = tuple(Candidate(f"{CANDIDATE_PREFIX}{first + n}", x.how, where.file, x.line, where.text(x.line), x.reads)
                       for n, x in enumerate(rows[k] for k in sorted(rows)))
    return Gap(f"{GAP_PREFIX}{number}", name, origin, line, at, candidates, reached.over_budget)


def _body(reached: list[Reached], created: Node, where: Where) -> Body | None:
    site = enclosing_method(created)
    for line in (x for r in reached for x in r.lines):
        method = enclosing_method(line.node) if line.node is not None else None
        if method is not None and method is not site:
            start = max(method.line, min(line.line - BODY_LINES // 2, method.end_line - BODY_LINES + 1))
            end = min(method.end_line, start + BODY_LINES - 1)
            return Body(where.file, start, tuple(where.lines[start - 1:end]))
    return None


def _asked(reading: Reading, engines: Engines, where: Where, found: Found) -> list[tuple[tuple, Reached]]:
    asked = []
    for r in sorted(reading.values, key=_order):
        if r.open:
            reached = reach(reading.values[r], engines)
            closed = reached.settled
            if closed is not None:
                found.settled[r.key] = Completion(closed.reads, closed.line, where.file, CODE_SOURCE)
            else:
                asked.append((r.key, reached))
    if _LOST_USE in reading.lifecycle.reasons:
        asked.append(((USE_GAP, UNKNOWN_ORIGIN, where.line, where.line), use_lines(reading.created, reading.binding, {s.line for s in reading.lifecycle.steps})))
    return asked


def _capped(reached: Reached) -> Reached:
    return Reached([], True, True) if reached.lines else reached


def gaps_of(reading: Reading, engines: Engines, where: Where) -> Found:
    found = Found()
    if reading.created is None:
        return found
    asked = _asked(reading, engines, where, found)
    if not asked:
        return found
    rows, first = [], 1
    kept = [(key, r if n < GAPS_PER_SCOPE else _capped(r)) for n, (key, r) in enumerate(asked)]
    for number, (key, r) in enumerate(kept, 1):
        rows.append(_gap(number, key, r, first, where))
        first += len(rows[-1].candidates)
    steps = {s.line for s in reading.lifecycle.steps}
    found.gaps = ScopeGaps(where.scope, where.file, where.function, Statement(where.line, where.text(where.line)),
                           tuple(Statement(n, where.text(n)) for n in sorted(steps)), tuple(rows),
                           _body([r for _, r in kept], reading.created, where))
    return found
