"""dossiers.json against scopes.json, groups.json and the app's screen verdicts."""
from __future__ import annotations

from collections import Counter

from ...dto.change import DROP_IN, MIGRATION
from ...dto.dossier import BROKEN_USE, NO_REAL_USE, Dossier
from ...dto.interop import pair_status
from ...dto.lifecycle import NO_REAL_USE as NO_REAL_USE_STATUS
from ...dto.perf_mode import PerfMode
from ...dto.screen import ACCEPTED, BROKEN, Verdict, refused_target
from ...dto.site import Scope
from .document import check_header, check_no_options, check_not_offered, perf_of
from .dossier import check_dossier, raw_scope_id


def _screen(where: str, d: Dossier, verdicts: dict[str, Verdict] | None) -> list[str]:
    if verdicts is None:
        return [f"{where} {o.alias}: screen {o.screen!r} without screen.json; it is null"
                for o in d.options if o.screen is not None]
    problems = []
    for o in d.options:
        status = verdicts[o.item].status if o.item in verdicts else None
        if o.screen != status:
            problems.append(f"{where} {o.alias}: screen {o.screen!r} is not this app's status {status!r}")
        if refused_target(verdicts.get(d.current), verdicts.get(o.item)):
            problems.append(f"{where} {o.alias}: {o.item} is {status}, refused as a target of {d.current}")
    return problems


def _upgrade_row(raw, app, perf: PerfMode, verdicts: dict[str, Verdict] | None) -> list[str]:
    """A broken use's candidates: an accepted item only, whatever its class; no_gain never applies."""
    d, problems = check_dossier(raw, app, perf, MIGRATION, gained=False)
    if d is None:
        return problems
    where, v = f"upgrade {d.key}", verdicts or {}
    if d.current not in v or v[d.current].status != BROKEN:
        problems.append(f"{where}: current {d.current} is not broken")
    return problems + [f"{where} {o.alias}: {o.item} is not accepted" for o in d.options
                       if o.item not in v or v[o.item].status != ACCEPTED or o.screen != ACCEPTED]


def _upgrades(doc: dict, app, perf: PerfMode, verdicts: dict[str, Verdict] | None) -> list[str]:
    rows = [r for r in doc.get("upgrades") or []]
    listed = {raw_scope_id(r) for r in rows}
    marked = {n["scope"] for n in doc.get("noOptions") or [] if isinstance(n, dict) and n.get("reason") == BROKEN_USE}
    problems = [f"scope {s}: an upgrades row needs the noOptions reason {BROKEN_USE}" for s in sorted(listed - marked, key=str)]
    problems += [f"scope {s}: noOptions {BROKEN_USE} without an upgrades row" for s in sorted(marked - listed, key=str)]
    return problems + [p for r in rows for p in _upgrade_row(r, app, perf, verdicts)]


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
    seen = Counter([raw_scope_id(raw) for raw in doc.get("dossiers") or []] + no_options)
    problems += [f"scope {s} appears {n} times" for s, n in sorted(seen.items(), key=str) if n > 1]
    problems += [f"scope {s}: not in scopes.json" for s in sorted(set(seen) - set(by_id), key=str)]
    problems += [f"scope {s}: neither a dossier nor in noOptions" for s in sorted(set(by_id) - set(seen))]
    problems += _unused_reasons(doc, scopes) + _upgrades(doc, doc.get("app"), perf, verdicts)
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


def _drop_ins_in_group(where: str, d: Dossier, group_of: dict, group: str | None) -> list[str]:
    drop_ins = [o for o in d.options if o.change == DROP_IN]
    problems = [f"{where}: current {d.current} is not a grouped item"] if group is None and drop_ins else []
    return problems + [f"{where} {o.alias}: {o.item} is not another member of group {group}"
                       for o in drop_ins if o.item == d.current or group_of.get(o.item) != group]


def _others_outside_group(where: str, d: Dossier, group_of: dict, group: str | None) -> list[str]:
    if group is None:
        return []
    return [f"{where} {o.alias}: {o.change} {o.item} is in the current item's group {group}"
            for o in d.options if o.change != DROP_IN and group_of.get(o.item) == group and not (o.diff and o.diff.addsDependency)]


def _in_group(where: str, d: Dossier, groups: dict) -> list[str]:
    """A drop-in is another member of the current item's group; any other class is outside it."""
    group_of = {v["qualified"]: v.get("group") for v in groups["items"].values()}
    group = group_of.get(d.current)
    problems = _drop_ins_in_group(where, d, group_of, group) + _others_outside_group(where, d, group_of, group)
    return problems + [f"{where} {o.alias}: interop {o.interop} is not the groups.json status {status}"
                       for o in d.options if o.interop != (status := pair_status(groups, d.current, o.item))]
