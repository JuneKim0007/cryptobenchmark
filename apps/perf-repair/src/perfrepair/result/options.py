"""Joined: one variant's groups, rows and verdicts; a scope's current item, options and candidates not offered, or why none."""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from ..catalog.names import fold, same_engine
from ..dto import PrimitiveRow, Summary
from ..dto.change import (
    NO_GAIN,
    NOT_LISTED,
    PROVIDER_PATH,
    RECOMMENDATION,
    REJECTED,
    SAME_ENGINE,
    Change,
    PairDiff,
    output_changes,
)
from ..dto.dossier import (
    CROSS_SESSION,
    CURRENT_NOT_MEASURED,
    NO_SECURE_OPTION,
    OPTION_PREFIX,
    PERSON_JUDGES,
    ZERO_MEDIAN,
    Option,
)
from ..dto.grouping import provider_of, qualified
from ..dto.interop import failed_pairs, pair_status
from ..dto.perf_mode import PerfMode, no_evidence
from ..dto.screen import ACCEPTED, BROKEN, Verdict, refused_target
from ..dto.site import Scope
from .candidates import Family
from .change import foreign_member, needs_review, reach
from .configurations import Config, cross_session, estimates, nearest, operations, pins
from .gain import no_gain
from .upgrades import measured_enough, rank

BY_ORDER = "resolved_by_order"


def _targets(current: str, others: list[str], usable: list[str], failed: set,
             verdicts: dict[str, Verdict] | None) -> tuple[list[str], str | None]:
    """The options left after each filter, or the reason of the first filter that leaves none."""
    if not usable:
        return [], "none_available" if others else "no_alternative"
    v = verdicts or {}
    allowed = [q for q in usable if not refused_target(v.get(current), v.get(q))]
    if not allowed:
        return [], "deprecated_only"
    # data from before a failed swap does not decrypt after it, so such a pair is never an option
    interoperable = [q for q in allowed if frozenset((current, q)) not in failed]
    return interoperable, None if interoperable else "interop_failed"


def _weighable(o: Option) -> set[str]:
    # a zero median was measured: the option shows why it has no ratio, while another kind of energy is no evidence
    return {e.metric for e in o.estimates} | {n.metric for n in o.noEstimates if n.reason == ZERO_MEDIAN}


def _missing(options: list[Option], perf: PerfMode) -> dict[str, tuple[str, ...]]:
    """Per option, the required metrics it has no estimate of."""
    return {o.alias: tuple(m.name for m in perf.required if m.name not in _weighable(o)) for o in options}


def _evidenced(options: list[Option], perf: PerfMode) -> tuple[list[Option], str | None]:
    """The options with an estimate of every required metric, and of one at least, renumbered; else the no_evidence reason.
    Generic requires none, so an option with some metrics is weighed, one with none never reaches the model."""
    missing = _missing(options, perf)
    kept = [o for o in options if not missing[o.alias] and _weighable(o)]
    if not kept:
        lacking = {m for names in missing.values() for m in names} or set(perf.names)
        return [], no_evidence(sorted(lacking, key=perf.names.index))
    return [replace(o, alias=f"{OPTION_PREFIX}{n}") for n, o in enumerate(kept, 1)], None


@dataclass(frozen=True)
class Joined:
    """What every scope's dossier is joined from: groups, the measured rows of one variant by item, their summaries, the app's
    screen verdicts (None without screen.json), the perfMode whose metrics alone are estimated, and the family
    candidates beyond the group (None: drop-in only, nothing classed)."""
    groups: dict
    measured: dict[str, dict[Config, PrimitiveRow]]
    measurements: dict[str, dict[str, Summary | None]]
    verdicts: dict[str, Verdict] | None
    perf: PerfMode
    available: set[str]
    family: Family | None = None

    def _track(self, current: str, q: str, change: Change | None) -> str:
        """Both providers real for the app, one canonical name, the group's output: a swap of provider only."""
        moved = provider_of(q) != provider_of(current) and {provider_of(q), provider_of(current)} <= self.available
        mine, theirs = self._canonical(current), self._canonical(q)
        same = None not in (mine, theirs) and fold(mine) == fold(theirs)
        return PROVIDER_PATH if change is None and moved and same else RECOMMENDATION

    def option(self, s: Scope, current: str, n: int, q: str, change: Change | None = None, by_order: bool = False) -> Option:
        mine, theirs = self.measured.get(current, {}), self.measured[q]
        configs = nearest(s, mine, theirs)
        # no configuration measured on both sides: the pins are unknown, never guessed
        pinned = pins(mine[configs[0]], theirs[configs[0]]) if configs else None
        # a site that only decrypts is shown decrypt numbers; pins do not depend on the operation
        used = nearest(s, mine, theirs, operations(s))
        sides = (used, mine, theirs, self.measurements, self.perf.names)
        classed = {"change": change.change, "diff": change.diff} if change is not None else {}
        found, absent = estimates(*sides)
        d = change.diff if change is not None else None
        rows = (self.family.row(current), self.family.row(q)) if self.family else (None, None)
        return Option(f"{OPTION_PREFIX}{n}", q, pinned, pair_status(self.groups, current, q), found,
                      None if self.verdicts is None else self.verdicts[q].status, absent, **classed,
                      outputChanges=output_changes(d), reach=reach(s),
                      needsReview=needs_review(s, d, *rows) + (BY_ORDER,) * by_order
                      + (CROSS_SESSION,) * cross_session(used, mine, theirs), track=self._track(current, q, change))

    def others(self, current: str) -> list[str] | None:
        """The other members of the current item's group; None when it is in none."""
        items = self.groups["items"]
        key = next((k for k, v in items.items() if v["qualified"] == current), None)
        group = items[key].get("group") if key is not None else None
        if group is None:
            return None
        members = next(g["members"] for g in self.groups["groups"] if g["id"] == group)
        return sorted(items[str(m)]["qualified"] for m in members if str(m) != key)

    def _runs(self, q: str) -> bool:
        entry = next((v for v in self.groups["items"].values() if v["qualified"] == q), None)
        return bool(entry and entry.get("runs"))

    def _usable(self, q: str) -> bool:
        return self._runs(q) and provider_of(q) in self.available

    def _foreign(self, q: str) -> bool:
        return provider_of(q) not in self.available

    def _measured_here(self, q: str) -> bool:
        return self._runs(q) and bool(self.measured.get(q))

    def _canonical(self, q: str) -> str | None:
        if self.family is not None:
            return self.family.canonical_of.get(q)
        v = (self.verdicts or {}).get(q)
        return v.canonical if v is not None else None

    def same_engine(self, current: str, q: str) -> bool:
        return same_engine(current, q, self._canonical(current), self._canonical(q))

    def _refused(self, current: str, q: str) -> bool:
        v = self.verdicts or {}
        return refused_target(v.get(current), v.get(q))

    def changes(self, s: Scope, current: str, others: list[str] | None) -> list[Change]:
        """Every candidate beyond a drop-in, classed: the family's, and a group member only the harness has."""
        if self.family is None:
            return []
        members = [foreign_member(s, q) for q in others or () if self._foreign(q) and self._measured_here(q)]
        return members + self.family.classed(s, current, set(others or ()), self._measured_here,
                                             lambda q: self._refused(current, q), self._foreign)

    def _drop_in(self, current: str, others: list[str] | None) -> tuple[list[str], str | None]:
        if others is None:
            return [], "not_grouped"
        usable = [q for q in others if self._usable(q)]
        return _targets(current, others, usable, failed_pairs(self.groups), self.verdicts)

    def _gained(self, s: Scope, built: list[Option]) -> tuple[list[Option], list[Change]]:
        """No option with one metric proven worse and none better, whatever its class; each dropped one kept with its reason."""
        lost = [o for o in built if no_gain(o.estimates)]
        return [o for o in built if o not in lost], [Change(o.item, REJECTED, o.diff or PairDiff.same(reach(s)), (NO_GAIN,)) for o in lost]

    def broken(self, current: str | None) -> bool:
        v = (self.verdicts or {}).get(current)
        return v is not None and v.status == BROKEN

    def _accepted(self, q: str) -> bool:
        v = (self.verdicts or {}).get(q)
        return v is not None and v.status == ACCEPTED

    def _listed(self, current: str, q: str) -> bool:
        return fold(self._canonical(q) or q) in self.family.targets(current)

    def own_numbers(self, s: Scope, options: list[Option]) -> dict[str, dict[str, float | None]]:
        """Each option's own medians at this site, by the rank's reading; a metric it has none of is None."""
        keys = {o.item: rank(s, self.measured[o.item], self.measurements, self.perf) for o in options}
        return {q: {m: v if isfinite(v) else None for m, v in zip(self.perf.names, key)} for q, key in keys.items()}

    def identified(self, current: str, options: list[Option]) -> bool:
        """The upgrade list names this current's targets: its options are the list's, and no model is needed."""
        return self.family is not None and any(self._listed(current, o.item) for o in options)

    def _candidates(self, s: Scope, current: str) -> tuple[list[Change], list[Change]]:
        """(offered, kept): the family's accepted items no class rejects, whatever maxChange; the list's when it has any."""
        changes = self.family.classed(s, current, set(), self._measured_here, lambda q: not self._accepted(q), self._foreign)
        rejected = [c for c in changes if c.change == REJECTED]
        offered = [c for c in changes if c.change != REJECTED]
        listed = [c for c in offered if self._listed(current, c.item)]
        if not listed:
            return offered, rejected
        return listed, rejected + [Change(c.item, REJECTED, c.diff, (NOT_LISTED,)) for c in offered if c not in listed]

    def _nothing_ranked(self, s: Scope, kept: list[Change]) -> str:
        """An accepted, measured member under a reject reason is a person's to weigh; only with none is there no secure option."""
        def weighable(c: Change) -> bool:
            return (self._accepted(c.item) and self._measured_here(c.item)
                    and measured_enough(rank(s, self.measured[c.item], self.measurements, self.perf), self.perf))
        reasons = sorted({r for c in kept if weighable(c) for r in c.reasons})
        return f"{PERSON_JUDGES}: {', '.join(reasons)}" if reasons else NO_SECURE_OPTION

    def _upgrade(self, s: Scope, current: str, by_order: bool) -> tuple[str, list[Option], str | None, list[Change]]:
        """A broken current: its candidates by measured performance in the mode's metrics; no_gain never applies."""
        if self.family is None:
            return current, [], NO_SECURE_OPTION, []
        offered, kept = self._candidates(s, current)
        keys = {c.item: rank(s, self.measured[c.item], self.measurements, self.perf) for c in offered}
        unmeasured = [c for c in offered if not measured_enough(keys[c.item], self.perf)]
        kept += [Change(c.item, REJECTED, c.diff, ("not_measured",)) for c in unmeasured]
        ranked = sorted((c for c in offered if c not in unmeasured),
                        key=lambda c: (c.diff.addsDependency, keys[c.item], c.item))
        if not ranked:
            return current, [], self._nothing_ranked(s, kept), kept
        return current, [self.option(s, current, n, c.item, c, by_order) for n, c in enumerate(ranked, 1)], None, kept

    def options(self, s: Scope, on: str | None = None, by_order: bool = False) -> tuple[str, list[Option], str | None, list[Change]]:
        """The scope's current item on provider `on` (the scope's own when None), options and the candidates not offered,
        or the reason of the first filter that leaves no option: the drop-in reason when no other class is offered either."""
        current = qualified(s.engineType, s.algorithm, on or s.provider)
        if self.broken(current):
            return self._upgrade(s, current, by_order)
        others = self.others(current)
        alias = [q for q in others or () if self.same_engine(current, q)]
        targets, reason = self._drop_in(current, None if others is None else [q for q in others if q not in alias])
        offered, kept = self.family.split(self.changes(s, current, others)) if self.family else ([], [])
        kept += [Change(q, REJECTED, PairDiff.same(reach(s)), (SAME_ENGINE,)) for q in alias]
        if not targets and not offered:
            return current, [], reason, kept
        if not self.measured.get(current):
            return current, [], CURRENT_NOT_MEASURED, kept
        built = [self.option(s, current, n, q, by_order=by_order) for n, q in enumerate(targets, 1)]
        built += [self.option(s, current, n, c.item, c, by_order) for n, c in enumerate(offered, len(built) + 1)]
        gained, lost = self._gained(s, built)
        if not gained:
            return current, [], NO_GAIN, kept + lost
        options, missing = _evidenced(gained, self.perf)
        return current, options, missing, kept + lost
