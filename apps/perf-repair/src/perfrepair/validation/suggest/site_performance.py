"""The performance part of the replacement gate: what a pick's code-computed labels allow under the unit's perfMode, and
a recommend's and concerns' shape. A listed perfMode keeps the strict rule; generic lets the model accept a trade-off it
names."""
from __future__ import annotations

from ...dto.dossier import Option
from ...dto.metrics import NAMES
from ...dto.perf_mode import PerfMode
from ...dto.replacement import MAX_CONCERN_LENGTH, MAX_CONCERNS
from ...result.gain import IMPROVED, WORSE, by_change, strict_passes


def _named(raw, field: str) -> tuple[list[str], list[str]]:
    if not isinstance(raw, list) or not all(isinstance(m, str) for m in raw):
        return [], [f"{field} is not a list of metric names"]
    return raw, [f"{field}: {m!r} is not one of {list(NAMES)}" for m in raw if m not in NAMES]


def metric_fields(d: dict) -> tuple[list[str], list[str], list[str]]:
    """deciding and accepted as given, and their problems; absent is empty."""
    deciding, p1 = _named(d.get("deciding", []), "deciding")
    accepted, p2 = _named(d.get("accepted", []), "accepted")
    return deciding, accepted, p1 + p2


def concerns_of(d: dict) -> tuple[list[str], list[str]]:
    raw = d.get("concerns", [])
    if not isinstance(raw, list) or not all(isinstance(c, str) for c in raw):
        return [], ["concerns is not a list of strings"]
    problems = [f"concerns holds {len(raw)}, at most {MAX_CONCERNS}"] if len(raw) > MAX_CONCERNS else []
    problems += [f"concerns[{i}] is longer than {MAX_CONCERN_LENGTH} characters" for i, c in enumerate(raw) if len(c) > MAX_CONCERN_LENGTH]
    return [c.strip() for c in raw if c.strip()], problems


def _generic(alias: str, o: Option, deciding: list[str], accepted: list[str]) -> list[str]:
    better, worse = by_change(o.estimates, IMPROVED), by_change(o.estimates, WORSE)
    if not better:
        return [f"{alias} improves no metric beyond noise; generic picks only an option that improves one"]
    problems = [] if deciding else ["a generic replace names its deciding metrics"]
    problems += [f"deciding metric {m} did not improve for {alias} (improved: {', '.join(better)})" for m in deciding if m not in better]
    return problems + [f"{alias} is worse on {m}; name it in accepted" for m in worse if m not in accepted]


def performance(perf: PerfMode, picks: list[tuple[str, Option]], deciding: list[str], accepted: list[str]) -> list[str]:
    """picks: each replaced member's chosen option, by member alias."""
    if perf.overall:
        return [p for alias, o in picks for p in _generic(f"{alias} {o.alias}", o, deciding, accepted)]
    problems = [f"{alias} {o.alias} breaks perfMode {perf.name}'s rule: a selected metric must improve and none worsen"
                for alias, o in picks if not strict_passes(o.estimates)]
    return problems + ([f"accepted {accepted}: perfMode {perf.name} accepts no loss"] if accepted else [])


def recommendable(alias: str, o: Option | None, needs) -> list[str]:
    """A recommend names an option with a change line and what would have to change."""
    if o is None:
        return []
    problems = [] if o.diff is not None else [f"{alias} {o.alias} has no change line; a like-for-like option is a replace or a keep"]
    ok = isinstance(needs, list) and all(isinstance(n, str) and n.strip() for n in needs) and needs
    return problems + ([] if ok else [f"{alias}: a recommend lists its needs"])
