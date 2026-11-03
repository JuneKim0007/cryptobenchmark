"""dossiers.json: the one validator; the replace stage parses with the same per-dossier checks."""
from __future__ import annotations

import math
from collections import Counter

from ..dto.grouping import parse_qualified
from ..dto.change import CHANGES, CLASSES, DROP_IN, REJECT_REASONS, REJECTED, admits
from ..dto.interop import PAIR_STATUSES, pair_status
from ..dto.screen import STATUSES, Verdict, lowers_status
from ..dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ..dto.perf_mode import PerfMode
from ..dto.site import (DOSSIERS_SCHEMA_VERSION, NO_ESTIMATE_REASONS, NO_OPTION_REASONS, NO_REAL_USE, OPTION_PREFIX,
                        Dossier, Scope, reason_code)
from ..dto.unit import PairInterop, Stay, Unit, UnitDossiers
from .app import scope_problems

KEYS = {"schemaVersion", "app", "perfMode", "maxChange", "dossiers", "noOptions", "notOffered", "units"}
NOT_OFFERED_KEYS = {"scope", "item", "change", "diff", "reasons"}


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
    problems += [f"{k} is not a list" for k in ("dossiers", "noOptions", "notOffered", "units")
                 if not isinstance(doc.get(k), list)]
    if doc.get("maxChange") not in CHANGES:
        problems.append(f"maxChange {doc.get('maxChange')!r} is not one of {CHANGES}")
    if perf_of(doc) is None:
        problems.append(f"perfMode {doc.get('perfMode')!r} does not parse")
    return problems + ([] if isinstance(doc.get("app"), str) else ["app is not a string"])


def perf_of(doc: dict) -> PerfMode | None:
    try:
        return PerfMode.parse(doc.get("perfMode"))
    except (ValueError, AttributeError):
        return None


def check_no_options(doc: dict) -> list[str]:
    problems = []
    for i, n in enumerate(doc.get("noOptions") or []):
        if not isinstance(n, dict) or set(n) != {"scope", "reason"} or not isinstance(n["scope"], str):
            problems.append(f"noOptions[{i}]: is not a {{scope, reason}} object")
        elif not isinstance(n["reason"], str) or reason_code(n["reason"]) not in NO_OPTION_REASONS:
            problems.append(f"noOptions {n['scope']}: reason {n['reason']!r} is not one of {NO_OPTION_REASONS}")
    return problems


def check_not_offered(doc: dict) -> list[str]:
    """A candidate not offered is rejected with reasons, or of a class above maxChange: a recommendation."""
    problems, top = [], doc.get("maxChange")
    for i, n in enumerate(doc.get("notOffered") or []):
        where = f"notOffered[{i}]"
        if not isinstance(n, dict) or set(n) != NOT_OFFERED_KEYS:
            problems.append(f"{where}: keys are not {sorted(NOT_OFFERED_KEYS)}")
        elif n["change"] not in CLASSES:
            problems.append(f"{where}: change {n['change']!r} is not one of {CLASSES}")
        elif (n["change"] == REJECTED) != bool(n["reasons"]) or not set(n["reasons"]) <= set(REJECT_REASONS):
            problems.append(f"{where}: reasons {n['reasons']!r} are not reject reasons of a rejected candidate")
        elif top in CHANGES and admits(top, n["change"]):
            problems.append(f"{where}: {n['change']} is within maxChange {top}; it is an option")
    return problems


def _changes(where: str, d: Dossier, max_change: str) -> list[str]:
    """Each option within maxChange; a drop-in carries no diff, any other class carries one."""
    problems = [f"{where} {o.alias}: change {o.change!r} is above maxChange {max_change}" for o in d.options
                if not admits(max_change, o.change)]
    return problems + [f"{where} {o.alias}: {o.change} {'with' if o.diff else 'without'} a pair diff" for o in d.options
                       if (o.diff is None) != (o.change == DROP_IN)]


def _estimates(where: str, d: Dossier, selected: tuple[str, ...]) -> list[str]:
    problems = []
    for o in d.options:
        for e in o.estimates:
            at = f"{where} {o.alias} {e.metric}"
            if e.metric not in selected:
                problems.append(f"{at}: metric is not one of the perfMode's {selected}")
            if not (_number(e.ratio) and e.ratio > 0):
                problems.append(f"{at}: ratio {e.ratio!r} is not a positive number")
            p, n = e.pImprove, e.n
            if not isinstance(n, int) or n < 1:
                problems.append(f"{at}: n {n!r} is not a positive integer")
            elif (p is None) != (n < 2):
                problems.append(f"{at}: pImprove {p!r} with n {n}; only fewer than two runs leave it empty")
            if p is not None and not (_number(p) and 0 <= p <= 1):
                problems.append(f"{at}: pImprove {p!r} is not a probability")
    return problems + _no_estimates(where, d, selected)


def _no_estimates(where: str, d: Dossier, selected: tuple[str, ...]) -> list[str]:
    return [f"{where} {o.alias} {n.metric}: no-estimate reason {n.reason!r} is not one of {NO_ESTIMATE_REASONS}, or the "
            f"metric is not selected" for o in d.options for n in o.noEstimates
            if n.reason not in NO_ESTIMATE_REASONS or n.metric not in selected]


def check_dossier(raw, app: str | None, perf: PerfMode, max_change: str = DROP_IN) -> tuple[Dossier | None, list[str]]:
    """One dossier on its own: its scope, its items, its aliases R1..Rn, its pins, interop labels, estimates of
    perf's metrics only and change classes within max_change."""
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
    return d, problems + _labels(where, d) + _estimates(where, d, perf.names) + _changes(where, d, max_change)


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
    if not isinstance(doc, dict) or (perf := perf_of(doc)) is None:
        return problems
    if "interop" not in groups:
        return problems + ["groups.json has no interop section; rerun grouping report"]
    problems += check_no_options(doc) + check_not_offered(doc)
    by_id = {s.id: s for s in scopes}
    no_options = [n["scope"] for n in doc.get("noOptions") or [] if isinstance(n, dict) and "scope" in n]
    seen = Counter([_id(raw) for raw in doc.get("dossiers") or []] + no_options)
    problems += [f"scope {s} appears {n} times" for s, n in sorted(seen.items(), key=str) if n > 1]
    problems += [f"scope {s}: not in scopes.json" for s in sorted(set(seen) - set(by_id), key=str)]
    problems += [f"scope {s}: neither a dossier nor in noOptions" for s in sorted(set(by_id) - set(seen))]
    problems += _unused_reasons(doc, scopes)
    for raw in doc.get("dossiers") or []:
        problems += _against_run(raw, doc.get("app"), perf, by_id, groups, verdicts, doc.get("maxChange", DROP_IN))
    return problems


def _against_run(raw, app, perf: PerfMode, by_id: dict[str, Scope], groups: dict, verdicts: dict[str, Verdict] | None,
                 max_change: str) -> list[str]:
    """One dossier against scopes.json, groups.json and the screen verdicts."""
    d, problems = check_dossier(raw, app, perf, max_change)
    if d is None:
        return problems
    where = f"dossier {d.key}"
    if d.scope.id in by_id and d.scope != by_id[d.scope.id]:
        problems.append(f"{where}: scope differs from scopes.json")
    return problems + _in_group(where, d, groups) + _screen(where, d, verdicts)


def _in_group(where: str, d: Dossier, groups: dict) -> list[str]:
    """A drop-in is another member of the current item's group; any other class is outside it."""
    group_of = {v["qualified"]: v.get("group") for v in groups["items"].values()}
    group = group_of.get(d.current)
    drop_ins = [o for o in d.options if o.change == DROP_IN]
    problems = [f"{where}: current {d.current} is not a grouped item"] if group is None and drop_ins else []
    problems += [f"{where} {o.alias}: {o.item} is not another member of group {group}"
                 for o in drop_ins if o.item == d.current or group_of.get(o.item) != group]
    problems += [f"{where} {o.alias}: {o.change} {o.item} is in the current item's group {group}"
                 for o in d.options if o.change != DROP_IN and group is not None and group_of.get(o.item) == group]
    return problems + [f"{where} {o.alias}: interop {o.interop} is not the groups.json status {status}"
                       for o in d.options if o.interop != (status := pair_status(groups, d.current, o.item))]


def _grouped(doc: dict, dossiers: list[Dossier], none: dict[str, str]) -> tuple[list[UnitDossiers], list[str]]:
    """Each asked unit with its members' dossiers and stays, in member order; every dossier in exactly one unit."""
    by_key = {d.key: d for d in dossiers}
    items, problems = [], []
    for raw in doc["units"]:
        item, found = _unit_item(raw, by_key, none)
        problems += found
        if item is not None:
            items.append(item)
    return items, problems + _membership(items, by_key, not problems)


def _membership(items: list[UnitDossiers], by_key: dict[str, Dossier], complete: bool) -> list[str]:
    members = Counter(m for item in items for m in item.unit.members)
    unplaced = [f"dossier {k}: in no unit" for k in by_key if members[k] == 0] if complete else []
    return unplaced + [f"dossier {k}: in {n} units" for k, n in members.items() if n > 1]


def _stays(unit: Unit, stays: tuple[Stay, ...], by_key: dict[str, Dossier], none: dict[str, str]) -> list[str]:
    where = f"unit {unit.id}"
    problems = [] if any(m in by_key for m in unit.members) else [f"{where}: no member has a dossier"]
    if [s.scope for s in stays] != [m for m in unit.members if m not in by_key]:
        problems.append(f"{where}: stays are not exactly its members without a dossier, in member order")
    return problems + [f"{where}: {s.scope} stays for {s.reason!r}, not its noOptions reason {none.get(s.scope)!r}"
                       for s in stays if none.get(s.scope) != s.reason]


def _unit_item(raw, by_key: dict[str, Dossier], none: dict[str, str]) -> tuple[UnitDossiers | None, list[str]]:
    try:
        unit = Unit.from_json(raw)
        stays = tuple(Stay.from_json(s) for s in raw["stays"])
        pairs = tuple(PairInterop.from_json(p) for p in raw["pairs"])
    except (KeyError, TypeError) as e:
        return None, [f"unit: does not parse: {e!r}"]
    problems = _stays(unit, stays, by_key, none)
    problems += [f"unit {unit.id}: pair {p.a} and {p.b}: interop {p.status!r} is not one of {PAIR_STATUSES}"
                 for p in pairs if p.status not in PAIR_STATUSES]
    if problems:
        return None, problems
    return UnitDossiers(unit, tuple(by_key[m] for m in unit.members if m in by_key), stays, pairs), []


def parse_dossiers(doc: dict, app: str) -> tuple[list[UnitDossiers], dict[str, str], list[str]]:
    """The units asked with their dossiers, each noOptions scope with its reason code, and every problem found."""
    problems = check_header(doc)
    if problems:
        return [], {}, problems
    if doc["app"] != app:
        return [], {}, [f"dossiers are for app {doc['app']!r}, not {app!r}"]
    problems, perf = check_no_options(doc) + check_not_offered(doc), perf_of(doc)
    dossiers = []
    for raw in doc["dossiers"]:
        d, found = check_dossier(raw, app, perf, doc["maxChange"])
        problems += found
        if d is not None:
            dossiers.append(d)
    none = {n["scope"]: n["reason"] for n in doc["noOptions"] if isinstance(n, dict) and "scope" in n}
    keys = Counter([d.key for d in dossiers] + [n.get("scope") for n in doc["noOptions"] if isinstance(n, dict)])
    problems += [f"{k}: scope appears more than once" for k, n in sorted(keys.items(), key=str) if n > 1]
    items, grouping = _grouped(doc, dossiers, none)
    return items, none, problems + grouping
