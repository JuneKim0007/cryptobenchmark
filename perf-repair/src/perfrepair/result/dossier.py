"""Scopes + groups + measurements → one Dossier per scope with options, or the reason it has none."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path

from ..dto import PrimitiveRow, Summary
from ..dto.grouping import parse_qualified, qualified
from ..dto.interop import failed_pairs, pair_status
from ..dto.screen import Verdict, lowers_status
from ..dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ..dto.measurement import ESTIMATED
from ..dto.perf_mode import PerfMode, no_evidence
from ..dto.metrics import BY_NAME
from ..dto.site import (DOSSIERS_SCHEMA_VERSION, NO_REAL_USE, NOT_ON_DEVICE, OPTION_PREFIX, Dossier,
                        Estimate, NoEstimate, Option, Scope, reason_code)
from ..dto.change import DROP_IN, NO_GAIN, REJECTED, Change, PairDiff
from .candidates import Family
from .change import foreign_member, reach
from .estimate import compare
from .gain import no_gain
from ..stop.halt import Coded

RESOLVED = ("default", "explicit")

Config = tuple  # (operation, keySize, inputSize, phase)


def _config(r: PrimitiveRow) -> Config:
    return r.operation, r.keySize, r.inputSize, r.phase


def label(c: Config) -> str:
    return f"{c[0]} key {c[1]} input {c[2]} {c[3]}"


def nearest(scope: Scope, current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow],
            operations: tuple[str, ...] = ()) -> list[Config]:
    """Configurations both measured at the scope's key size and the closest input size; every size when unknown.
    operations: only these, when given."""
    shared = [c for c in current if c in option and scope.keySize in (None, c[1]) and (not operations or c[0] in operations)]
    if scope.inputSize is None or not shared:
        return sorted(shared, key=str)
    gap = min(abs((c[2] or 0) - scope.inputSize) for c in shared)
    return sorted((c for c in shared if abs((c[2] or 0) - scope.inputSize) == gap), key=str)


def operations(scope: Scope) -> tuple[str, ...]:
    """The operations the lifecycle performs; empty, meaning every one, when it does not know."""
    return scope.lifecycle.operations if scope.lifecycle is not None else ()


def pins(current: PrimitiveRow, option: PrimitiveRow) -> dict:
    """The option's parameters that differ from the current ones."""
    keys = sorted(set(current.parameters) | set(option.parameters))
    return {k: option.parameters.get(k) for k in keys if current.parameters.get(k) != option.parameters.get(k)}


def _sides(configs: list[Config], current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow],
           measurements: dict[str, dict[str, Summary | None]], metrics: tuple[str, ...]):
    for c in configs:
        for metric in metrics:
            before = (measurements.get(current[c].rowId) or {}).get(metric)
            after = (measurements.get(option[c].rowId) or {}).get(metric)
            if before is not None and after is not None:
                yield c, metric, compare(before, after, BY_NAME[metric].lowerIsBetter), after.kind


def _shown(c: Config, kind: str | None) -> str:
    # the words reach the decision through the configuration it is already shown
    return f"{label(c)}, estimated" if kind == ESTIMATED else label(c)


def estimates(*sides) -> tuple[tuple[Estimate, ...], tuple[NoEstimate, ...]]:
    """Each metric both sides have: an estimate, or the reason code compare() gives no ratio, so the decision sees why."""
    found = list(_sides(*sides))
    return (tuple(Estimate(metric, e.ratio, e.pImprove, e.n, _shown(c, kind), kind) for c, metric, e, kind in found
                  if e.ratio is not None),
            tuple(NoEstimate(metric, label(c), reason_code(e.reason)) for c, metric, e, _ in found if e.ratio is None))


def function_source(root: Path, scope: Scope) -> str:
    lines = (Path(root) / scope.file).read_text(errors="replace").splitlines()
    return "\n".join(lines[scope.start - 1:scope.end])


def _targets(current: str, others: list[str], usable: list[str], failed: set,
             verdicts: dict[str, Verdict] | None) -> tuple[list[str], str | None]:
    """The options left after each filter, or the reason of the first filter that leaves none."""
    if not usable:
        return [], "none_available" if others else "no_alternative"
    v = verdicts or {}
    allowed = [q for q in usable if not lowers_status(v.get(current), v.get(q))]
    if not allowed:
        return [], "deprecated_only"
    # data from before a failed swap does not decrypt after it, so such a pair is never an option
    interoperable = [q for q in allowed if frozenset((current, q)) not in failed]
    return interoperable, None if interoperable else "interop_failed"


def _missing(options: list[Option], perf: PerfMode) -> dict[str, tuple[str, ...]]:
    """Per option, the required metrics it has no estimate of; generic requires none."""
    return {o.alias: tuple(m.name for m in perf.required if m.name not in {e.metric for e in o.estimates}) for o in options}


def _evidenced(options: list[Option], perf: PerfMode) -> tuple[list[Option], str | None]:
    """The options with an estimate of every required metric, renumbered; else the no_evidence reason."""
    missing = _missing(options, perf)
    kept = [o for o in options if not missing[o.alias]]
    if not kept:
        return [], no_evidence(sorted({m for names in missing.values() for m in names}, key=perf.names.index))
    return [replace(o, alias=f"{OPTION_PREFIX}{n}") for n, o in enumerate(kept, 1)], None


def _unresolved(s: Scope) -> str | None:
    if s.lifecycle is not None and s.lifecycle.status == NO_REAL_USE_STATUS:
        return NO_REAL_USE
    if s.resolution == NOT_ON_DEVICE:
        return NOT_ON_DEVICE
    return None if s.resolution in RESOLVED and s.algorithm is not None and s.provider is not None else "unresolved"


@dataclass(frozen=True)
class Joined:
    """What every scope's dossier is joined from: groups, the measured rows by item, their summaries, the app's
    screen verdicts (None without screen.json), the perfMode whose metrics alone are estimated, and the family
    candidates beyond the group (None: drop-in only, nothing classed)."""
    groups: dict
    measured: dict[str, dict[Config, PrimitiveRow]]
    measurements: dict[str, dict[str, Summary | None]]
    verdicts: dict[str, Verdict] | None
    perf: PerfMode
    available: set[str]
    family: Family | None = None

    def option(self, s: Scope, current: str, n: int, q: str, change: Change | None = None) -> Option:
        mine, theirs = self.measured[current], self.measured[q]
        configs = nearest(s, mine, theirs)
        # no configuration measured on both sides: the pins are unknown, never guessed
        pinned = pins(mine[configs[0]], theirs[configs[0]]) if configs else None
        # a site that only decrypts is shown decrypt numbers; pins do not depend on the operation
        used = nearest(s, mine, theirs, operations(s))
        sides = (used, mine, theirs, self.measurements, self.perf.names)
        classed = {"change": change.change, "diff": change.diff} if change is not None else {}
        found, absent = estimates(*sides)
        return Option(f"{OPTION_PREFIX}{n}", q, pinned, pair_status(self.groups, current, q), found,
                      None if self.verdicts is None else self.verdicts[q].status, absent, **classed)

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
        return self._runs(q) and parse_qualified(q)[2] in self.available

    def _foreign(self, q: str) -> bool:
        return parse_qualified(q)[2] not in self.available

    def _measured_here(self, q: str) -> bool:
        return self._runs(q) and bool(self.measured.get(q))

    def _lowers(self, current: str, q: str) -> bool:
        v = self.verdicts or {}
        return lowers_status(v.get(current), v.get(q))

    def changes(self, s: Scope, current: str, others: list[str] | None) -> list[Change]:
        """Every candidate beyond a drop-in, classed: the family's, and a group member only the harness has."""
        if self.family is None:
            return []
        members = [foreign_member(s, q) for q in others or () if self._foreign(q) and self._measured_here(q)]
        return members + self.family.classed(s, current, set(others or ()), lambda q: parse_qualified(q)[2], self._measured_here,
                                             lambda q: self._lowers(current, q), self._foreign)

    def _drop_in(self, current: str, others: list[str] | None) -> tuple[list[str], str | None]:
        if others is None:
            return [], "not_grouped"
        usable = [q for q in others if self._usable(q)]
        return _targets(current, others, usable, failed_pairs(self.groups), self.verdicts)

    def _gained(self, s: Scope, built: list[Option]) -> tuple[list[Option], list[Change]]:
        """No option worse on every selected metric, whatever its class; each dropped one kept with its reason."""
        lost = [o for o in built if no_gain(o.estimates)]
        return [o for o in built if o not in lost], [Change(o.item, REJECTED, o.diff or PairDiff.same(reach(s)), (NO_GAIN,)) for o in lost]

    def options(self, s: Scope) -> tuple[str, list[Option], str | None, list[Change]]:
        """The scope's current item, options and the candidates not offered, or the reason of the first filter that
        leaves no option: the drop-in reason when no other class is offered either."""
        current = qualified(s.engineType, s.algorithm, s.provider)
        others = self.others(current)
        targets, reason = self._drop_in(current, others)
        offered, kept = self.family.split(self.changes(s, current, others)) if self.family else ([], [])
        if not targets and not offered:
            return current, [], reason, kept
        built = [self.option(s, current, n, q) for n, q in enumerate(targets, 1)]
        built += [self.option(s, current, n, c.item, c) for n, c in enumerate(offered, len(built) + 1)]
        gained, lost = self._gained(s, built)
        if not gained:
            return current, [], NO_GAIN, kept + lost
        options, missing = _evidenced(gained, self.perf)
        return current, options, missing, kept + lost


def available_providers(platform: frozenset[str], harness: dict[str, str], app_doc: dict) -> set[str]:
    """What the app's process has: the device's own and what the app ships; harness: per provider providers.bundled
    installed, its group:name, the same library under the harness's own name counting as shipped."""
    shipped = app_doc.get("bundled") or []
    names = {b["providerName"] for b in shipped if b.get("providerName")}
    artifacts = {b["artifact"] for b in shipped}
    return {*platform, *names, *(p for p, artifact in harness.items() if artifact in artifacts)}


def build_dossiers(app: str, scopes: list[Scope], app_doc: dict, groups: dict, rows: list[PrimitiveRow],
                   measurements: dict[str, dict[str, Summary | None]], source_root: Path,
                   verdicts: dict[str, Verdict] | None, perf: PerfMode, family: Family | None = None,
                   available: set[str] | None = None) -> dict:
    """verdicts: each item's screen verdict for this app by qualified name; None without screen.json.
    perf: only its metrics are estimated, and an option without one it requires is dropped.
    family: the type catalog's candidates beyond the group up to its maxChange; None offers drop-ins only.
    available: the providers in the app's process; None, without a probe: every probed one and what the app ships."""
    bare = sorted(r.rowId for r in rows if r.parameters is None)
    if bare:
        raise Coded(f"missing_parameters: rows {', '.join(bare)} report no parameters; the benchmark always writes them")
    if available is None:
        available = {parse_qualified(v["qualified"])[2] for v in groups["items"].values()}
        available |= {b["providerName"] for b in app_doc.get("bundled") or []}
    measured: dict[str, dict[Config, PrimitiveRow]] = defaultdict(dict)
    for r in rows:
        measured[qualified(r.type, r.algorithm, r.provider)][_config(r)] = r
    joined = Joined(groups, measured, measurements, verdicts, perf, available, family)
    dossiers, none, kept = [], [], []
    for s in scopes:
        current, options, reason, others = (None, [], _unresolved(s), []) if _unresolved(s) else joined.options(s)
        kept += [{"scope": s.id, **c.to_json()} for c in others]
        if reason is not None:
            none.append({"scope": s.id, "reason": reason})
            continue
        dossiers.append(Dossier(s, function_source(source_root, s), current, tuple(options)))
    return {"schemaVersion": DOSSIERS_SCHEMA_VERSION, "app": app, "perfMode": perf.to_json(),
            "maxChange": family.max_change if family else DROP_IN, "dossiers": [d.to_json() for d in dossiers],
            "noOptions": none, "notOffered": kept, "units": []}
