from __future__ import annotations

from collections import Counter

from ...dto.grouping import KEY_CONTRACTS, Item, Profile
from ...catalog.families import ANY_TYPE, Families


def validate_items(items: list[Item], profiles: dict[int, Profile], families: Families) -> list[str]:
    problems = []
    ids = [i.id for i in items]
    if ids != list(range(1, len(items) + 1)):
        problems.append(f"ids are not 1..{len(items)} in order")
    problems += [f"{q}: {n} items" for q, n in Counter(i.qualified for i in items).items() if n > 1]
    for i in items:
        family = families.by_id.get(i.family)
        if family is None:
            problems.append(f"{i.id}: family {i.family!r} is not in the catalog")
        elif family.type not in (i.type, ANY_TYPE):
            problems.append(f"{i.id}: family {i.family} is for {family.type}, not {i.type}")
        elif i.id in profiles and family.keyKind != profiles[i.id].keyKind:
            problems.append(f"{i.id}: family {i.family} is for key kind {family.keyKind}, profile says {profiles[i.id].keyKind}")
        if not (i.type and i.name and i.provider):
            problems.append(f"{i.id}: type, name or provider is empty")
    problems += [f"{n}: no profile" for n in ids if n not in profiles]
    problems += [f"{n}: profile for no item" for n in profiles if n not in set(ids)]
    return problems + _key_contract_problems(profiles)


def _key_contract_problems(profiles: dict[int, Profile]) -> list[str]:
    return [f"{n}: key contract {p.keyContract!r} is not one of {KEY_CONTRACTS}"
            for n, p in profiles.items() if p.keyContract not in KEY_CONTRACTS]
