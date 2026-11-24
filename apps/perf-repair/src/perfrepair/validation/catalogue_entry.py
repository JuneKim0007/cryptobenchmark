"""Static checks of a catalogue entry: its form, family against engine type, one id across the catalogues, the names file's canonical name."""
from __future__ import annotations

from cryptobench.shared.catalogue.algorithms import Algorithms, Entry, canonical_problems, entry_problems, split_id
from cryptobench.shared.catalogue.families import Families
from cryptobench.shared.catalogue.glossary import provider_key_problems, term_problems
from cryptobench.shared.catalogue.names import Names, fold


def entry_check(entry: Entry, catalogue: Algorithms, families: Families, names: Names) -> list[str]:
    """catalogue holds the entry: a new one is checked inside the catalogues it would join."""
    found = entry_problems(entry, catalogue.common) + term_problems(entry.raw) + provider_key_problems(entry.raw)
    family, parts = families.by_id.get(entry.family), split_id(entry.id)
    if family is None:
        found.append(f"family {entry.family} is not a family of families.yaml")
    elif parts is not None and parts[0] != family.type:
        found.append(f"engine type {parts[0]} does not fit family {entry.family} ({family.type})")
    found += canonical_problems(entry, names) if parts is not None else []
    held = sorted(e.family for e in catalogue.entries if fold(e.id) == fold(entry.id))
    return found + [f"id is in {len(held)} catalogues: {held}"] * (len(held) != 1)


def catalogue_check(catalogue: Algorithms, families: Families, names: Names) -> list[str]:
    """Every entry's problems, each as `<family> <id>: <problem>`."""
    return [f"{e.family} {e.id}: {p}" for e in catalogue.entries for p in entry_check(e, catalogue, families, names)]
