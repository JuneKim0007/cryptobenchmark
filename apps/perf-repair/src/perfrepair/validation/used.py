"""used.json: every item is a device item named once, by a known way, for apps the document lists."""
from __future__ import annotations

from collections import Counter

from ..dto.used import VIA, UsedItem, UsedSet


def _item(u: UsedItem, items: set[str], apps: dict) -> list[str]:
    return [p for p in (
        f"item {u.item}: not in items.json" if u.item not in items else "",
        f"item {u.item}: via {u.via!r} is not one of {list(VIA)}" if u.via not in VIA else "",
        f"item {u.item}: no app needs it" if not u.apps else "",
        *(f"item {u.item}: app {a} is not listed" for a in u.apps if a not in apps)) if p]


def validate_used(used: UsedSet, items: set[str]) -> list[str]:
    problems = [f"item {q}: listed {n} times" for q, n in Counter(u.item for u in used.items).items() if n > 1]
    problems += [p for u in used.items for p in _item(u, items, used.apps)]
    problems += [f"app {a}: {u.matched} matched of {u.sites} sites" for a, u in used.apps.items()
                 if not 0 <= u.matched <= u.sites]
    if used.deviceItems != len(items):
        problems.append(f"deviceItems {used.deviceItems}, items.json holds {len(items)}")
    return problems
