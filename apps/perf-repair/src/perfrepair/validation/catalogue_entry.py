"""Static checks of a catalogue entry: its form, family against engine type, one id across the catalogues, one group."""
from __future__ import annotations

from ..catalog.algorithms import (
    Algorithms,
    Entry,
    algorithm_id,
    entry_problems,
    split_id,
)
from ..catalog.families import Families
from ..catalog.glossary import provider_key_problems, term_problems
from ..catalog.groups import GroupCatalog
from ..catalog.names import fold


def _group_count(groups: GroupCatalog, families: Families, identifier: str) -> int:
    return sum(1 for g in groups.families if g.family in families.by_id
               and fold(identifier) in {fold(algorithm_id(families.by_id[g.family].type, n)) for n in g.algorithms})


def entry_check(entry: Entry, catalogue: Algorithms, groups: GroupCatalog, families: Families) -> list[str]:
    """catalogue holds the entry: a new one is checked inside the catalogues it would join."""
    found = entry_problems(entry, catalogue.common) + term_problems(entry.raw) + provider_key_problems(entry.raw)
    family, parts = families.by_id.get(entry.family), split_id(entry.id)
    if family is None:
        found.append(f"family {entry.family} is not a family of families.yaml")
    elif parts is not None and parts[0] != family.type:
        found.append(f"engine type {parts[0]} does not fit family {entry.family} ({family.type})")
    held = sorted(e.family for e in catalogue.entries if fold(e.id) == fold(entry.id))
    found += [f"id is in {len(held)} catalogues: {held}"] * (len(held) != 1)
    listed = _group_count(groups, families, entry.id)
    return found + [f"id is in {listed} groups, not one"] * (listed != 1)


def catalogue_check(catalogue: Algorithms, groups: GroupCatalog, families: Families) -> list[str]:
    """Every entry's problems, each as `<family> <id>: <problem>`."""
    return [f"{e.family} {e.id}: {p}" for e in catalogue.entries for p in entry_check(e, catalogue, groups, families)]
