"""Scopes + groups + measurements → one Dossier per scope with options, or the reason it has none."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..dto import PrimitiveRow, Summary
from ..dto.grouping import parse_qualified, qualified
from ..dto.interop import failed_pairs, pair_status
from ..dto.site import METRICS, SCHEMA_VERSION, Dossier, Estimate, Option, Scope
from .estimate import compare

RESOLVED = ("default", "explicit")
MEASUREMENT_KEY = {"allocationCount": "allocations"}

Config = tuple  # (operation, keySize, inputSize, phase)


def _config(r: PrimitiveRow) -> Config:
    return r.operation, r.keySize, r.inputSize, r.phase


def label(c: Config) -> str:
    return f"{c[0]} key {c[1]} input {c[2]} {c[3]}"


def nearest(scope: Scope, current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow]) -> list[Config]:
    """Configurations both measured at the scope's key size and the closest input size; every size when unknown."""
    shared = [c for c in current if c in option and scope.keySize in (None, c[1])]
    if scope.inputSize is None or not shared:
        return sorted(shared, key=str)
    gap = min(abs((c[2] or 0) - scope.inputSize) for c in shared)
    return sorted((c for c in shared if abs((c[2] or 0) - scope.inputSize) == gap), key=str)


def pins(current: PrimitiveRow, option: PrimitiveRow) -> dict:
    """The option's parameters that differ from the current ones."""
    keys = sorted(set(current.parameters) | set(option.parameters))
    return {k: option.parameters.get(k) for k in keys if current.parameters.get(k) != option.parameters.get(k)}


def estimates(configs: list[Config], current: dict[Config, PrimitiveRow], option: dict[Config, PrimitiveRow],
              measurements: dict[str, dict[str, Summary | None]]) -> tuple[Estimate, ...]:
    out = []
    for c in configs:
        for metric in METRICS:
            key = MEASUREMENT_KEY.get(metric, metric)
            before = (measurements.get(current[c].rowId) or {}).get(key)
            after = (measurements.get(option[c].rowId) or {}).get(key)
            if before is None or after is None or before.median == 0:
                continue
            e = compare(before, after)
            out.append(Estimate(metric, e.ratio, e.pImprove, e.n, label(c)))
    return tuple(out)


def function_source(root: Path, scope: Scope) -> str:
    lines = (Path(root) / scope.file).read_text(errors="replace").splitlines()
    return "\n".join(lines[scope.start - 1:scope.end])


def build_dossiers(app: str, scopes: list[Scope], app_doc: dict, groups: dict, rows: list[PrimitiveRow],
                   measurements: dict[str, dict[str, Summary | None]], source_root: Path) -> dict:
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
        if s.resolution not in RESOLVED or s.algorithm is None or s.provider is None:
            none.append({"scope": s.id, "reason": "unresolved"})
            continue
        current = qualified(s.engineType, s.algorithm, s.provider)
        key = by_qualified.get(current)
        group = items[key].get("group") if key is not None else None
        if group is None:
            none.append({"scope": s.id, "reason": "not_grouped"})
            continue
        others = sorted(items[m]["qualified"] for m in members[group] if m != key)
        usable = [q for q in others if items[by_qualified[q]].get("runs") and parse_qualified(q)[2] in available]
        if not usable:
            none.append({"scope": s.id, "reason": "none_available" if others else "no_alternative"})
            continue
        # data from before a failed swap does not decrypt after it, so such a pair is never an option
        interoperable = [q for q in usable if frozenset((current, q)) not in failed]
        if not interoperable:
            none.append({"scope": s.id, "reason": "interop_failed"})
            continue
        options = []
        for n, q in enumerate(interoperable, 1):
            configs = nearest(s, measured[current], measured[q])
            # no configuration measured on both sides: the pins are unknown, never guessed
            pinned = pins(measured[current][configs[0]], measured[q][configs[0]]) if configs else None
            options.append(Option(f"R{n}", q, pinned, pair_status(groups, current, q),
                                  estimates(configs, measured[current], measured[q], measurements)))
        dossiers.append(Dossier(s, function_source(source_root, s), current, tuple(options)))
    return {"schemaVersion": SCHEMA_VERSION, "app": app, "dossiers": [d.to_json() for d in dossiers],
            "noOptions": none}
