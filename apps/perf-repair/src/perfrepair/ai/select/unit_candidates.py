"""A unit's candidates, by code: each item every member with options offers, applicable under maxChange with known pins,
passing the perfMode's rule, its inverse links kept readable; the risks each swap carries, and whether code can apply it."""
from __future__ import annotations

from ...dto.change import SAME, admits
from ...dto.dossier import Option
from ...dto.perf_mode import PerfMode
from ...dto.replacement import OUTPUT_LEAVES, required_risks
from ...dto.unit import INVERSE, UnitDossiers
from ...result.gain import IMPROVED, by_change, strict_passes
from .candidate import RECOMMEND, REPLACE, Candidate, Pick

UNVERIFIED = "unverified_interop"


def passes(perf: PerfMode, o: Option) -> bool:
    """strict: a selected metric improves and none worsens; overall: some metric improves beyond noise."""
    return bool(by_change(o.estimates, IMPROVED)) if perf.overall else strict_passes(o.estimates)


def _shared(u: UnitDossiers) -> list[str]:
    """The items every member with options offers, in the first member's order."""
    offered = [[o.item for o in d.options] for d in u.dossiers]
    return [i for i in offered[0] if all(i in rest for rest in offered[1:])]


def _stay_problem(u: UnitDossiers, item: str, swapped: set[str]) -> tuple[bool, set[str]]:
    """An inverse link from a swapped member to one that stays: refused on a failed pair or another output, else the
    swapped sides that must declare unverified_interop."""
    stays, unverified = {s.scope: s.current for s in u.stays}, set()
    outputs = {d.key: next(o for o in d.options if o.item == item) for d in u.dossiers}
    for k in (k for k in u.unit.links if k.kind == INVERSE):
        moved = [m for m in (k.a, k.b) if m in swapped]
        other = next((m for m in (k.a, k.b) if m in stays), None)
        if not moved or other is None:
            continue
        o = outputs[moved[0]]
        status = u.interop(item, stays[other])
        if (o.diff is not None and o.diff.output != SAME) or status == "fail":
            return True, set()
        unverified |= set(moved) if status != "pass" else set()
    return False, unverified


def unit_candidates(u: UnitDossiers, perf: PerfMode, max_change: str) -> list[Candidate]:
    aliases, found = u.aliases(), []
    for item in _shared(u):
        picks = [(d, next(o for o in d.options if o.item == item)) for d in u.dossiers]
        if any(o.pins is None or not admits(max_change, o.change) or not passes(perf, o) for _, o in picks):
            continue
        refused, unverified = _stay_problem(u, item, {d.key for d, _ in picks})
        if refused:
            continue
        built = tuple(Pick(aliases[d.key], d, o, tuple(required_risks(d.scope, o)) + ((UNVERIFIED,) * (
            d.key in unverified and UNVERIFIED not in required_risks(d.scope, o)))) for d, o in picks)
        leaving = sorted({r for p in built if p.option.outputChanges for r in p.risks if r in OUTPUT_LEAVES})
        needs = tuple(f"{r}: what reads this output must follow the new one" for r in leaving)
        found.append(Candidate(f"C{len(found) + 1}", item, RECOMMEND if leaving else REPLACE, built, needs))
    return found
