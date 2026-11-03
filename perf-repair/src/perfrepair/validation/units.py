"""units.json: every scope in one unit, ids recomputed, members connected by their links, each line a link cites taken
from that side's lifecycle."""
from __future__ import annotations

from ..dto.unit import LINK_VIA, UNITS_SCHEMA_VERSION, unit_id

_UNIT_KEYS = {"id", "members", "links", "sharedFunction"}
_LINK_KEYS = {"kind", "a", "b", "aLines", "bLines", "via"}


def _lifecycle_lines(scope: dict) -> set[int]:
    lc = scope.get("lifecycle") or {}
    lines = {t.get("line") for t in lc.get("steps") or []}
    for r in lc.get("requirements") or []:
        lines |= {r.get("line"), r.get("at")}
    return lines


def _link(where: str, k, members: set[str], by_id: dict[str, dict]) -> list[str]:
    if not isinstance(k, dict) or set(k) != _LINK_KEYS:
        return [f"{where}: a link is not {sorted(_LINK_KEYS)}"]
    if k["kind"] not in LINK_VIA or k["via"] not in LINK_VIA[k["kind"]]:
        return [f"{where}: kind {k['kind']!r} via {k['via']!r} is not in {LINK_VIA}"]
    problems = [f"{where}: link side {side} is not a member" for side in (k["a"], k["b"]) if side not in members]
    if k["a"] == k["b"]:
        problems.append(f"{where}: a link of {k['a']} to itself")
    for side, lines in ((k["a"], k["aLines"]), (k["b"], k["bLines"])):
        if not lines:
            problems.append(f"{where}: link side {side} cites no line")
        elif side in by_id:
            problems += [f"{where}: line {n} is not in the lifecycle of {side}" for n in lines
                         if n not in _lifecycle_lines(by_id[side])]
    return problems


def _connected(members: list[str], links: list[dict]) -> bool:
    reached, todo = set(), members[:1]
    while todo:
        at = todo.pop()
        if at not in reached:
            reached.add(at)
            todo += [k["b"] if k["a"] == at else k["a"] for k in links if at in (k["a"], k["b"])]
    return reached == set(members)


def _unit(u, app: str, by_id: dict[str, dict]) -> list[str]:
    if not isinstance(u, dict) or set(u) != _UNIT_KEYS:
        return [f"unit: is not {sorted(_UNIT_KEYS)}"]
    where = f"unit {u['id']}"
    members = u["members"]
    problems = [] if u["id"] == unit_id(app, members) else [f"{where}: id is not unit_id of its members"]
    problems += [f"{where}: member {m} is not in scopes.json" for m in members if m not in by_id]
    for k in u["links"]:
        problems += _link(where, k, set(members), by_id)
    if not problems and not _connected(members, u["links"]):
        problems.append(f"{where}: its members are not connected by its links")
    return problems


def validate_units(doc: dict, scopes: list[dict]) -> list[str]:
    problems = [] if doc.get("schemaVersion") == UNITS_SCHEMA_VERSION else [f"schemaVersion {doc.get('schemaVersion')}"]
    units = doc.get("units")
    if not isinstance(units, list) or not isinstance(doc.get("app"), str):
        return problems + ["app is not a string or units is not a list"]
    by_id = {s["id"]: s for s in scopes}
    for u in units:
        problems += _unit(u, doc["app"], by_id)
    if problems:
        return problems
    members = [m for u in units for m in u["members"]]
    problems += [f"scope {m}: in several units" for m in sorted(set(members)) if members.count(m) > 1]
    problems += [f"scope {m}: in no unit" for m in sorted(set(by_id) - set(members))]
    ids = {u["id"] for u in units}
    return problems + [f"unit {u['id']}: sharedFunction names {o}, not a unit" for u in units for o in u["sharedFunction"]
                       if o not in ids]
