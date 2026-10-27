from __future__ import annotations

import math
from collections import Counter

from ..dto.site import METRICS, Dossier, Scope
from ..result.dossier import NO_OPTION_REASONS, SCHEMA_VERSION

KEYS = {"schemaVersion", "app", "dossiers", "noOptions"}


def _estimates(where: str, d: dict) -> list[str]:
    problems = []
    for o in d["options"]:
        for e in o.get("estimates") or []:
            at = f"{where} {o['alias']} {e.get('metric')}"
            if e.get("metric") not in METRICS:
                problems.append(f"{at}: metric is not one of {METRICS}")
            if not (isinstance(e.get("ratio"), (int, float)) and math.isfinite(e["ratio"]) and e["ratio"] > 0):
                problems.append(f"{at}: ratio {e.get('ratio')!r} is not a positive number")
            p, n = e.get("pImprove"), e.get("n")
            if not isinstance(n, int) or n < 1:
                problems.append(f"{at}: n {n!r} is not a positive integer")
            elif (p is None) != (n < 2):
                problems.append(f"{at}: pImprove {p!r} with n {n}; only fewer than two runs leave it empty")
            if p is not None and not 0 <= p <= 1:
                problems.append(f"{at}: pImprove {p} is not a probability")
    return problems


def validate_dossiers(doc: dict, scopes: list[Scope], groups: dict) -> list[str]:
    """dossiers.json against scopes.json and groups.json: every scope once, options from the current item's group."""
    problems = [] if set(doc) == KEYS else [f"keys {sorted(doc)} are not {sorted(KEYS)}"]
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    by_id = {s.id: s for s in scopes}
    group_of = {v["qualified"]: v.get("group") for v in groups["items"].values()}
    seen = Counter([d["scope"]["id"] for d in doc.get("dossiers") or []] + [n["scope"] for n in doc.get("noOptions") or []])
    problems += [f"scope {s} appears {n} times" for s, n in sorted(seen.items()) if n > 1]
    problems += [f"scope {s}: not in scopes.json" for s in sorted(set(seen) - set(by_id))]
    problems += [f"scope {s}: neither a dossier nor in noOptions" for s in sorted(set(by_id) - set(seen))]
    problems += [f"noOptions {n['scope']}: reason {n.get('reason')!r} is not one of {NO_OPTION_REASONS}"
                 for n in doc.get("noOptions") or [] if n.get("reason") not in NO_OPTION_REASONS]
    for raw in doc.get("dossiers") or []:
        d, where = Dossier.from_json(raw), f"dossier {raw['scope']['id']}"
        if d.scope.id in by_id and d.scope != by_id[d.scope.id]:
            problems.append(f"{where}: scope differs from scopes.json")
        group = group_of.get(d.current)
        if group is None:
            problems.append(f"{where}: current {d.current} is not a grouped item")
        if not d.options:
            problems.append(f"{where}: no options; such a scope belongs in noOptions")
        if [o.alias for o in d.options] != [f"R{n}" for n in range(1, len(d.options) + 1)]:
            problems.append(f"{where}: aliases are not R1..R{len(d.options)} in order")
        problems += [f"{where} {o.alias}: {o.item} is not another member of group {group}"
                     for o in d.options if o.item == d.current or group_of.get(o.item) != group]
        problems += _estimates(where, raw)
    return problems
