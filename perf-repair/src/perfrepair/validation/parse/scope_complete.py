"""Gate C of scope-complete: one answer per offered gap, a candidate offered to that gap or unknown, an origin on its list."""
from __future__ import annotations

from ...dto.gaps import UNKNOWN_CHOICE, UNKNOWN_ORIGIN, USE_GAP, USE_ORIGINS, Gap, ScopeGaps
from ...dto.lifecycle import OPEN_ORIGINS, ORIGINS
from ..json_reply import parse_object


def _origins(gap: Gap) -> tuple[str, ...]:
    return USE_ORIGINS if gap.name == USE_GAP else ORIGINS


def _choice_problems(n: int, a: dict, gap: Gap) -> list[str]:
    choice, origin = a.get("choice"), a.get("origin")
    if origin not in _origins(gap):
        return [f"answers[{n}]: origin {origin!r} is not one of {list(_origins(gap))} for {gap.id}"]
    if choice == UNKNOWN_CHOICE:
        return [] if origin == UNKNOWN_ORIGIN else [f"answers[{n}]: choice unknown takes origin unknown, not {origin!r}"]
    offered = {c.id: c for c in gap.candidates}
    if choice not in offered:
        return [f"answers[{n}]: choice {choice!r} is not offered to {gap.id}: {[*offered, UNKNOWN_CHOICE]}"]
    if origin == UNKNOWN_ORIGIN:
        return [f"answers[{n}]: a chosen line takes an origin other than unknown; answer choice unknown instead"]
    reads = offered[choice].reads
    if reads not in OPEN_ORIGINS and origin != reads:
        return [f"answers[{n}]: code reads {choice} as {reads}; origin {origin!r} differs from it"]
    return []


def _answer_problems(n: int, a, offered: dict[str, Gap], seen: set[str]) -> list[str]:
    if not isinstance(a, dict):
        return [f"answers[{n}] is not an object"]
    gap = offered.get(a.get("gap")) if isinstance(a.get("gap"), str) else None
    if gap is None:
        return [f"answers[{n}]: gap {a.get('gap')!r} is not one of {sorted(offered)}"]
    if gap.id in seen:
        return [f"answers[{n}]: gap {gap.id} is answered twice"]
    seen.add(gap.id)
    return _choice_problems(n, a, gap)


def check_reply(text: str, entry: ScopeGaps) -> tuple[dict | None, list[str]]:
    d, problems = parse_object(text)
    if d is None:
        return None, problems
    if not isinstance(d.get("answers"), list):
        return None, ["answers is not a list"]
    offered, seen = {g.id: g for g in entry.offered}, set()
    problems = [p for n, a in enumerate(d["answers"]) for p in _answer_problems(n, a, offered, seen)]
    problems += [f"gap {g} has no answer" for g in offered if g not in seen]
    if problems:
        return None, problems
    order = list(offered)
    return {"answers": [{"gap": a["gap"], "choice": a["choice"], "origin": a["origin"]}
                        for a in sorted(d["answers"], key=lambda a: order.index(a["gap"]))]}, []
