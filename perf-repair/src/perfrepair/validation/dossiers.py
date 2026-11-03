"""dossiers.json: the one validator; the replace stage parses with the same per-dossier checks."""
from __future__ import annotations

import math
from collections import Counter

from ..dto.grouping import parse_qualified
from ..dto.interop import PAIR_STATUSES, pair_status
from ..dto.screen import STATUSES, Verdict, lowers_status
from ..dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ..dto.site import (DOSSIERS_SCHEMA_VERSION, METRICS, NO_ESTIMATE_REASONS, NO_OPTION_REASONS, NO_REAL_USE, OPTION_PREFIX,
                        Dossier, Scope)
from ..dto.unit import Unit, UnitDossiers
from .app import scope_problems

KEYS = {"schemaVersion", "app", "dossiers", "noOptions", "units"}


def _id(raw) -> str | None:
    scope = raw.get("scope") if isinstance(raw, dict) else None
    return scope.get("id") if isinstance(scope, dict) else None


def _qualified(item) -> bool:
    try:
        parse_qualified(item)
    except (ValueError, AttributeError):
        return False
    return True


def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def check_header(doc) -> list[str]:
    if not isinstance(doc, dict):
        return ["dossiers.json is not an object"]
    problems = [] if set(doc) == KEYS else [f"keys {sorted(doc)} are not {sorted(KEYS)}"]
    if doc.get("schemaVersion") != DOSSIERS_SCHEMA_VERSION:
        problems.append(f"schemaVersion {doc.get('schemaVersion')} is not {DOSSIERS_SCHEMA_VERSION}")
    problems += [f"{k} is not a list" for k in ("dossiers", "noOptions", "units") if not isinstance(doc.get(k), list)]
    return problems + ([] if isinstance(doc.get("app"), str) else ["app is not a string"])


def check_no_options(doc: dict) -> list[str]:
    problems = []
    for i, n in enumerate(doc.get("noOptions") or []):
        if not isinstance(n, dict) or set(n) != {"scope", "reason"} or not isinstance(n["scope"], str):
            problems.append(f"noOptions[{i}]: is not a {{scope, reason}} object")
        elif n["reason"] not in NO_OPTION_REASONS:
            problems.append(f"noOptions {n['scope']}: reason {n['reason']!r} is not one of {NO_OPTION_REASONS}")
    return problems


def _estimates(where: str, d: Dossier) -> list[str]:
    problems = []
    for o in d.options:
        for e in o.estimates:
            at = f"{where} {o.alias} {e.metric}"
            if e.metric not in METRICS:
                problems.append(f"{at}: metric is not one of {METRICS}")
            if not (_number(e.ratio) and e.ratio > 0):
                problems.append(f"{at}: ratio {e.ratio!r} is not a positive number")
            p, n = e.pImprove, e.n
            if not isinstance(n, int) or n < 1:
                problems.append(f"{at}: n {n!r} is not a positive integer")
            elif (p is None) != (n < 2):
                problems.append(f"{at}: pImprove {p!r} with n {n}; only fewer than two runs leave it empty")
            if p is not None and not (_number(p) and 0 <= p <= 1):
                problems.append(f"{at}: pImprove {p!r} is not a probability")
    return problems + _no_estimates(where, d)


def _no_estimates(where: str, d: Dossier) -> list[str]:
    return [f"{where} {o.alias} {n.metric}: no-estimate reason {n.reason!r} is not one of {NO_ESTIMATE_REASONS}"
            for o in d.options for n in o.noEstimates if n.reason not in NO_ESTIMATE_REASONS]


def check_dossier(raw, app: str | None) -> tuple[Dossier | None, list[str]]:
    """One dossier on its own: its scope, its items, its aliases R1..Rn, its pins, interop labels and estimates."""
    where = f"dossier {_id(raw)}"
    if not isinstance(raw, dict):
        return None, [f"{where}: is not an object"]
    problems = scope_problems(where, raw.get("scope"), app)
    if problems:
        return None, problems
    try:
        d = Dossier.from_json(raw)
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        return None, [f"{where}: does not parse into Dossier: {e!r}"]
    if not isinstance(d.source, str) or not d.source.strip():
        problems.append(f"{where}: source is empty")
    items = [d.current] + [o.item for o in d.options]
    problems += [f"{where}: {item!r} is not a qualified item id" for item in items if not _qualified(item)]
    if not d.options:
        problems.append(f"{where}: no options; such a scope belongs in noOptions")
    if d.scope.lifecycle is not None and d.scope.lifecycle.status == NO_REAL_USE_STATUS:
        problems.append(f"{where}: lifecycle {NO_REAL_USE_STATUS}; such a scope belongs in noOptions as {NO_REAL_USE}")
    if [o.alias for o in d.options] != [f"{OPTION_PREFIX}{n}" for n in range(1, len(d.options) + 1)]:
        problems.append(f"{where}: aliases are not R1..R{len(d.options)} in order")
    if len(set(items)) != len(items):
        problems.append(f"{where}: an option repeats the current item or another option")
    problems += [f"{where} {o.alias}: screen {o.screen!r} is neither one of {STATUSES} nor null"
                 for o in d.options if o.screen is not None and o.screen not in STATUSES]
    return d, problems + _labels(where, d) + _estimates(where, d)


def _labels(where: str, d: Dossier) -> list[str]:
    problems = [f"{where} {o.alias}: pins {o.pins!r} is neither an object nor null (unknown)"
                for o in d.options if o.pins is not None and not isinstance(o.pins, dict)]
    problems += [f"{where} {o.alias}: interop {o.interop!r} is not one of {PAIR_STATUSES}"
                 for o in d.options if o.interop not in PAIR_STATUSES]
    problems += [f"{where} {o.alias}: interop fail; a failed pair is never an option"
                 for o in d.options if o.interop == "fail"]
    return problems


def _screen(where: str, d: Dossier, verdicts: dict[str, Verdict] | None) -> list[str]:
    if verdicts is None:
        return [f"{where} {o.alias}: screen {o.screen!r} without screen.json; it is null"
                for o in d.options if o.screen is not None]
    problems = []
    for o in d.options:
        status = verdicts[o.item].status if o.item in verdicts else None
        if o.screen != status:
            problems.append(f"{where} {o.alias}: screen {o.screen!r} is not this app's status {status!r}")
        if lowers_status(verdicts.get(d.current), verdicts.get(o.item)):
            problems.append(f"{where} {o.alias}: {o.item} is {status} and lowers the status of {d.current}")
    return problems


def _unused_reasons(doc: dict, scopes: list[Scope]) -> list[str]:
    reasons = {n["scope"]: n.get("reason") for n in doc.get("noOptions") or [] if isinstance(n, dict) and "scope" in n}
    unused = [s.id for s in scopes if s.lifecycle is not None and s.lifecycle.status == NO_REAL_USE_STATUS]
    return [f"scope {sid}: lifecycle {NO_REAL_USE_STATUS} but noOptions reason {reasons[sid]!r}" for sid in unused
            if sid in reasons and reasons[sid] != NO_REAL_USE]


def validate_dossiers(doc: dict, scopes: list[Scope], groups: dict, verdicts: dict[str, Verdict] | None) -> list[str]:
    """dossiers.json against scopes.json, groups.json and the app's screen verdicts (None without screen.json): every
    scope once, options from the current item's group labelled with the pair's interop status and the app's status."""
    problems = check_header(doc)
    if not isinstance(doc, dict):
        return problems
    if "interop" not in groups:
        return problems + ["groups.json has no interop section; rerun grouping report"]
    problems += check_no_options(doc)
    by_id = {s.id: s for s in scopes}
    group_of = {v["qualified"]: v.get("group") for v in groups["items"].values()}
    no_options = [n["scope"] for n in doc.get("noOptions") or [] if isinstance(n, dict) and "scope" in n]
    seen = Counter([_id(raw) for raw in doc.get("dossiers") or []] + no_options)
    problems += [f"scope {s} appears {n} times" for s, n in sorted(seen.items(), key=str) if n > 1]
    problems += [f"scope {s}: not in scopes.json" for s in sorted(set(seen) - set(by_id), key=str)]
    problems += [f"scope {s}: neither a dossier nor in noOptions" for s in sorted(set(by_id) - set(seen))]
    problems += _unused_reasons(doc, scopes)
    for raw in doc.get("dossiers") or []:
        d, found = check_dossier(raw, doc.get("app"))
        problems += found
        if d is None:
            continue
        where = f"dossier {d.key}"
        if d.scope.id in by_id and d.scope != by_id[d.scope.id]:
            problems.append(f"{where}: scope differs from scopes.json")
        group = group_of.get(d.current)
        if group is None:
            problems.append(f"{where}: current {d.current} is not a grouped item")
        problems += [f"{where} {o.alias}: {o.item} is not another member of group {group}"
                     for o in d.options if o.item == d.current or group_of.get(o.item) != group]
        problems += [f"{where} {o.alias}: interop {o.interop} is not the groups.json status {status}"
                     for o in d.options if o.interop != (status := pair_status(groups, d.current, o.item))]
        problems += _screen(where, d, verdicts)
    return problems


def _grouped(doc: dict, dossiers: list[Dossier]) -> tuple[list[UnitDossiers], list[str]]:
    """Each asked unit with its members' dossiers, in member order; every dossier in exactly one unit."""
    by_key = {d.key: d for d in dossiers}
    items, problems = [], []
    for raw in doc["units"]:
        try:
            unit = Unit.from_json(raw)
        except (KeyError, TypeError) as e:
            problems.append(f"unit: does not parse: {e!r}")
            continue
        missing = [m for m in unit.members if m not in by_key]
        problems += [f"unit {unit.id}: member {m} has no dossier" for m in missing]
        if not missing:
            items.append(UnitDossiers(unit, tuple(by_key[m] for m in unit.members)))
    members = Counter(m for item in items for m in item.unit.members)
    problems += [f"dossier {k}: in no unit" for k in by_key if members[k] == 0 and not problems]
    problems += [f"dossier {k}: in {n} units" for k, n in members.items() if n > 1]
    return items, problems


def parse_dossiers(doc: dict, app: str) -> tuple[list[UnitDossiers], dict[str, str], list[str]]:
    """The units asked with their dossiers, each noOptions scope with its reason code, and every problem found."""
    problems = check_header(doc)
    if problems:
        return [], {}, problems
    if doc["app"] != app:
        return [], {}, [f"dossiers are for app {doc['app']!r}, not {app!r}"]
    problems = check_no_options(doc)
    dossiers = []
    for raw in doc["dossiers"]:
        d, found = check_dossier(raw, app)
        problems += found
        if d is not None:
            dossiers.append(d)
    none = {n["scope"]: n["reason"] for n in doc["noOptions"] if isinstance(n, dict) and "scope" in n}
    keys = Counter([d.key for d in dossiers] + [n.get("scope") for n in doc["noOptions"] if isinstance(n, dict)])
    problems += [f"{k}: scope appears more than once" for k, n in sorted(keys.items(), key=str) if n > 1]
    items, grouping = _grouped(doc, dossiers)
    return items, none, problems + grouping
