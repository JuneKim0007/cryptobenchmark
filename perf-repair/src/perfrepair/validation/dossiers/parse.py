"""parse_dossiers: the units asked with their Dossiers and noOptions for the replace stage, by the same checks."""
from __future__ import annotations

from collections import Counter

from ...dto.dossier import Dossier
from ...dto.interop import PAIR_STATUSES
from ...dto.unit import PairInterop, Stay, Unit, UnitDossiers
from .document import check_header, check_no_options, check_not_offered, perf_of
from .dossier import check_dossier


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
