"""Scopes + groups + measurements → one Dossier per scope with options, or the reason it has none."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..dto import PrimitiveRow, Summary
from ..dto.grouping import parse_qualified, qualified
from ..dto.interop import failed_pairs, pair_status
from ..dto.screen import Verdict, lowers_status
from ..dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ..dto.measurement import ESTIMATED
from ..dto.site import (ENERGY_KINDS_DIFFER, METRICS, NO_REAL_USE, NOT_ON_DEVICE, OPTION_PREFIX, SCHEMA_VERSION, Dossier, Estimate,
                        NoEstimate, Option, Scope)
from .estimate import compare

RESOLVED = ("default", "explicit")
MEASUREMENT_KEY = {"allocationCount": "allocations"}

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
           measurements: dict[str, dict[str, Summary | None]]):
    for c in configs:
        for metric in METRICS:
            key = MEASUREMENT_KEY.get(metric, metric)
            before = (measurements.get(current[c].rowId) or {}).get(key)
            after = (measurements.get(option[c].rowId) or {}).get(key)
            if before is not None and after is not None and before.median != 0:
                yield c, metric, before, after


def _shown(c: Config, kind: str | None) -> str:
    # the words reach the decision through the configuration it is already shown
    return f"{label(c)}, estimated" if kind == ESTIMATED else label(c)


def estimates(*sides) -> tuple[Estimate, ...]:
    out = []
    for c, metric, before, after in _sides(*sides):
        if before.kind == after.kind:
            e = compare(before, after)
            out.append(Estimate(metric, e.ratio, e.pImprove, e.n, _shown(c, after.kind), after.kind))
    return tuple(out)


def no_estimates(*sides) -> tuple[NoEstimate, ...]:
    """A measured side and an estimated one are never one estimate."""
    return tuple(NoEstimate(metric, label(c), ENERGY_KINDS_DIFFER) for c, metric, before, after in _sides(*sides)
                 if before.kind != after.kind)


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


def _unresolved(s: Scope) -> str | None:
    if s.lifecycle is not None and s.lifecycle.status == NO_REAL_USE_STATUS:
        return NO_REAL_USE
    if s.resolution == NOT_ON_DEVICE:
        return NOT_ON_DEVICE
    return None if s.resolution in RESOLVED and s.algorithm is not None and s.provider is not None else "unresolved"


def build_dossiers(app: str, scopes: list[Scope], app_doc: dict, groups: dict, rows: list[PrimitiveRow],
                   measurements: dict[str, dict[str, Summary | None]], source_root: Path,
                   verdicts: dict[str, Verdict] | None) -> dict:
    """verdicts: each item's screen verdict for this app by qualified name; None without screen.json."""
    bare = sorted(r.rowId for r in rows if r.parameters is None)
    if bare:
        raise ValueError(f"missing_parameters: rows {', '.join(bare)} report no parameters; the benchmark always writes them")
    items, failed = groups["items"], failed_pairs(groups)
    by_qualified = {v["qualified"]: key for key, v in items.items()}
    members = {g["id"]: [str(m) for m in g["members"]] for g in groups["groups"]}
    # the probe lists what the platform registers; an app adds what it bundles
    available = {parse_qualified(v["qualified"])[2] for v in items.values()}
    available |= {b["providerName"] for b in app_doc.get("bundled") or []}
    measured: dict[str, dict[Config, PrimitiveRow]] = defaultdict(dict)
    for r in rows:
        measured[qualified(r.type, r.algorithm, r.provider)][_config(r)] = r

    dossiers, none = [], []
    for s in scopes:
        if unresolved := _unresolved(s):
            none.append({"scope": s.id, "reason": unresolved})
            continue
        current = qualified(s.engineType, s.algorithm, s.provider)
        key = by_qualified.get(current)
        group = items[key].get("group") if key is not None else None
        if group is None:
            none.append({"scope": s.id, "reason": "not_grouped"})
            continue
        others = sorted(items[m]["qualified"] for m in members[group] if m != key)
        usable = [q for q in others if items[by_qualified[q]].get("runs") and parse_qualified(q)[2] in available]
        targets, reason = _targets(current, others, usable, failed, verdicts)
        if reason is not None:
            none.append({"scope": s.id, "reason": reason})
            continue
        options = []
        for n, q in enumerate(targets, 1):
            configs = nearest(s, measured[current], measured[q])
            # no configuration measured on both sides: the pins are unknown, never guessed
            pinned = pins(measured[current][configs[0]], measured[q][configs[0]]) if configs else None
            # a site that only decrypts is shown decrypt numbers; pins do not depend on the operation
            used = nearest(s, measured[current], measured[q], operations(s))
            options.append(Option(f"{OPTION_PREFIX}{n}", q, pinned, pair_status(groups, current, q),
                                  estimates(used, measured[current], measured[q], measurements),
                                  None if verdicts is None else verdicts[q].status,
                                  no_estimates(used, measured[current], measured[q], measurements)))
        dossiers.append(Dossier(s, function_source(source_root, s), current, tuple(options)))
    return {"schemaVersion": SCHEMA_VERSION, "app": app, "dossiers": [d.to_json() for d in dossiers],
            "noOptions": none}
