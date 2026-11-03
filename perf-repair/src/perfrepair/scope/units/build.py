"""Units: the connected components of the links; a scope with none is a unit of one. units.json's document."""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from ...dto.site import Scope
from ...dto.unit import UNITS_SCHEMA_VERSION, Link, Unit, unit_id
from .links import links_of
from .shapes import Files


def _components(ids: list[str], links: list[Link]) -> list[list[str]]:
    parent = {i: i for i in ids}

    def find(i: str) -> str:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for k in links:
        parent[find(k.a)] = find(k.b)
    groups: dict[str, list[str]] = defaultdict(list)
    for i in ids:
        groups[find(i)].append(i)
    return list(groups.values())


def _with_shared_functions(units: list[Unit], by_id: dict[str, Scope]) -> list[Unit]:
    in_function: dict[tuple, set[str]] = defaultdict(set)
    for u in units:
        for m in u.members:
            in_function[(by_id[m].file, by_id[m].start, by_id[m].end)].add(u.id)
    out = []
    for u in units:
        spans = {(by_id[m].file, by_id[m].start, by_id[m].end) for m in u.members}
        others = set().union(*(in_function[span] for span in spans)) - {u.id}
        out.append(Unit(u.id, u.members, u.links, tuple(sorted(others))))
    return out


def build_units(app: str, scopes: list[Scope], root: Path) -> list[Unit]:
    ordered = sorted(scopes, key=lambda s: (s.file, s.line, s.id))
    links = links_of(ordered, Files(root))
    made = []
    for members in _components([s.id for s in ordered], links):
        inside = set(members)
        made.append(Unit(unit_id(app, members), tuple(members),
                         tuple(k for k in links if k.a in inside and k.b in inside)))
    return _with_shared_functions(made, {s.id: s for s in ordered})


def units_document(app: str, units: list[Unit]) -> dict:
    return {"schemaVersion": UNITS_SCHEMA_VERSION, "app": app, "units": [u.to_json() for u in units]}


def unit_counts(units: list[Unit]) -> dict:
    return {"units": len(units), "linked": sum(len(u.members) > 1 for u in units),
            "links": dict(sorted(Counter(k.kind for u in units for k in u.links).items())),
            "largest": max((len(u.members) for u in units), default=0)}
