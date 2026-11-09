from __future__ import annotations

from collections import Counter

from cryptobench.catalogue.grouping import Item, Profile, read_items, read_profiles
from ...dto.grouping_output import GROUPS_SCHEMA_VERSION
from ...dto.grouping_state import Group
from ...dto.screen import Verdict
from ...files import read_json
from ...run_dir import GroupingPaths
from ..failure import require
from ..screen import read_checked_screen
from .code_groups import validate_code_groups


def validate_output(doc: dict, items: dict[int, Item], screen: dict[int, Verdict] | None = None,
                    profiles: dict[int, Profile] | None = None) -> list[str]:
    """screen: screen.json's verdicts, None without it; a screened-out or catalog-listed item is placed without a model, never asked."""
    problems = []
    if doc.get("schemaVersion") != GROUPS_SCHEMA_VERSION:
        problems.append(f"schemaVersion {doc.get('schemaVersion')} is not {GROUPS_SCHEMA_VERSION}")
    problems += _placement(doc, items)
    if "interop" not in doc:
        problems.append("no interop section; rerun grouping report")
    if set(doc["items"]) != {str(i) for i in items}:
        problems.append("items index differs from items.json")
    problems += _screen_problems(doc, items, screen, profiles)
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


def _placement(doc: dict, items: dict[int, Item]) -> list[str]:
    """Each item in one group, dropped, or with used.json in notUsed; nothing else."""
    placed = Counter(m for g in doc["groups"] for m in g["members"])
    dropped, unused = {d["item"] for d in doc["dropped"]}, set(doc.get("notUsed") or ())
    problems = [f"item {m}: in {n} groups" for m, n in placed.items() if n > 1]
    problems += [f"item {m}: grouped and dropped" for m in dropped if m in placed]
    problems += [f"item {m}: notUsed and grouped or dropped" for m in unused & (set(placed) | dropped)]
    accounted = set(placed) | dropped | unused
    problems += [f"item {i}: neither grouped nor dropped" for i in items if i not in accounted]
    return problems + [f"item {m}: not in items.json" for m in accounted if m not in items]


def _screen_problems(doc: dict, items: dict[int, Item], screen: dict[int, Verdict] | None,
                     profiles: dict[int, Profile] | None) -> list[str]:
    status = {str(n): v.status for n, v in (screen or {}).items()}
    problems = [f"item {k}: screen {e.get('screen')!r}, screen.json says {status.get(k)!r}"
                for k, e in sorted(doc["items"].items()) if e.get("screen") != status.get(k)]
    groups = {g["id"]: Group(g["family"], g.get("description", ""), list(g["members"])) for g in doc["groups"]}
    return problems + validate_code_groups(groups, items, screen, profiles or {})


def read_groups(paths: GroupingPaths) -> dict:
    document = read_json(paths.groups)
    screen = read_checked_screen(paths)
    profiles = read_profiles(read_json(paths.profiles)) if screen is not None else {}
    require("groups.json", validate_output(document, {i.id: i for i in read_items(read_json(paths.items))}, screen, profiles))
    return document
