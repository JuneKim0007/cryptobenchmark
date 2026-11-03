"""used.json: every item is a device item named once, by a known way, for apps the document lists."""
from __future__ import annotations

from collections import Counter

from ..dto.used import VIA, UsedSet


def validate_used(used: UsedSet, items: set[str]) -> list[str]:
    problems = [f"item {q}: listed {n} times" for q, n in Counter(u.item for u in used.items).items() if n > 1]
    problems += [f"item {u.item}: not in items.json" for u in used.items if u.item not in items]
    problems += [f"item {u.item}: via {u.via!r} is not one of {list(VIA)}" for u in used.items if u.via not in VIA]
    problems += [f"item {u.item}: no app needs it" for u in used.items if not u.apps]
    problems += [f"item {u.item}: app {a} is not listed" for u in used.items for a in u.apps if a not in used.apps]
    problems += [f"app {a}: {u.matched} matched of {u.sites} sites" for a, u in used.apps.items()
                 if not 0 <= u.matched <= u.sites]
    if used.deviceItems != len(items):
        problems.append(f"deviceItems {used.deviceItems}, items.json holds {len(items)}")
    return problems
