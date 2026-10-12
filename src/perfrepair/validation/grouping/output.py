"""groups.json: every item either in exactly one group or dropped, never both; members and item ids agree
with items.json; every group's family is listed."""
from __future__ import annotations

from collections import Counter

from ...dto.grouping import Item
from ...dto.grouping_output import SCHEMA_VERSION


def validate_output(doc: dict, items: dict[int, Item]) -> list[str]:
    problems = []
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        problems.append(f"schemaVersion {doc.get('schemaVersion')} is not {SCHEMA_VERSION}")
    placed = Counter(m for g in doc["groups"] for m in g["members"])
    dropped = {d["item"] for d in doc["dropped"]}
    problems += [f"item {m}: in {n} groups" for m, n in placed.items() if n > 1]
    problems += [f"item {m}: grouped and dropped" for m in dropped if m in placed]
    problems += [f"item {i}: neither grouped nor dropped" for i in items if i not in placed and i not in dropped]
    problems += [f"item {m}: not in items.json" for m in set(placed) | dropped if m not in items]
    if set(doc["items"]) != {str(i) for i in items}:
        problems.append("items index differs from items.json")
    for g in doc["groups"]:
        if g["family"] not in doc["families"]:
            problems.append(f"group {g['id']}: family {g['family']} is not listed")
        for m in g["members"]:
            entry = doc["items"].get(str(m))
            if entry and entry["group"] != g["id"]:
                problems.append(f"item {m}: indexed under {entry['group']!r}, member of {g['id']!r}")
            if m in items and entry and entry["qualified"] != items[m].qualified:
                problems.append(f"item {m}: qualified name differs from items.json")
    return problems
