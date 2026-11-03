"""gaps.json: shape, closed lists, unique ids, cited lines inside the file, each gap naming an open requirement of its scope."""
from __future__ import annotations

from ..dto.gaps import CANDIDATE_PREFIX, GAP_PREFIX, HOWS, USE_GAP, Gap, ScopeGaps, read_gaps
from ..dto.lifecycle import OPEN_ORIGINS, ORIGINS, Lifecycle


def _candidate_problems(where: str, c, lines: int | None, seen: set[str]) -> list[str]:
    out = []
    if c.id in seen or not c.id.startswith(CANDIDATE_PREFIX):
        out.append(f"{where}: candidate id {c.id!r} is repeated or malformed")
    seen.add(c.id)
    if c.how not in HOWS or c.reads not in ORIGINS:
        out.append(f"{where}: {c.id}: how {c.how!r} or reads {c.reads!r} is off its list")
    if c.line < 1 or (lines is not None and c.line > lines):
        out.append(f"{where}: {c.id} cites line {c.line}, not a line of the file")
    return out


def _requirement_problem(where: str, gap: Gap, requirements: dict) -> list[str]:
    if gap.name == USE_GAP:
        return []
    if gap.requirement not in requirements:
        return [f"{where}: {gap.id} names no requirement of the scope: {gap.requirement}"]
    return [] if requirements[gap.requirement].open else [f"{where}: {gap.id} names the closed requirement {gap.requirement}"]


def _gap_problems(where: str, gap: Gap, requirements: dict, lines: int | None, seen: set[str]) -> list[str]:
    out = _requirement_problem(where, gap, requirements)
    if not gap.id.startswith(GAP_PREFIX) or gap.origin not in OPEN_ORIGINS:
        out.append(f"{where}: gap id {gap.id!r} or origin {gap.origin!r} is off its list")
    return out + [p for c in gap.candidates for p in _candidate_problems(where, c, lines, seen)]


def _entry_problems(e: ScopeGaps, scope: dict, lines: int | None) -> list[str]:
    lc = scope.get("lifecycle")
    requirements = {r.key: r for r in Lifecycle.from_json(lc).requirements} if lc else {}
    ids, seen = [g.id for g in e.gaps], set()
    out = [] if len(ids) == len(set(ids)) else [f"gaps {e.scope}: gap ids repeat: {ids}"]
    return out + [p for g in e.gaps for p in _gap_problems(f"gaps {e.scope}", g, requirements, lines, seen)]


def validate_gaps(doc: dict, scopes_doc: dict, lines: dict[str, int] | None = None) -> list[str]:
    """scopes_doc: the scopes.json beside it; lines: each source file's line count when the source is at hand."""
    try:
        entries = read_gaps(doc)
    except (KeyError, TypeError, ValueError) as e:
        return [f"gaps does not read: {e!r}"]
    out = [] if doc.get("app") == scopes_doc.get("app") else [f"gaps app {doc.get('app')!r} is not the scopes' {scopes_doc.get('app')!r}"]
    scopes = {s["id"]: s for s in scopes_doc["scopes"]}
    for e in entries:
        out += (_entry_problems(e, scopes[e.scope], (lines or {}).get(e.file)) if e.scope in scopes
                else [f"gaps: scope {e.scope} is not in scopes.json"])
    return out
