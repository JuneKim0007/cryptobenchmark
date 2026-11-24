"""A scope's candidates outside its current item's group: the items of its family under another canonical name, each
classed against the current type; those up to maxChange are offered, the others kept with their class or reasons."""
from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from cryptobench.shared.catalogue.names import fold
from ..catalog.types import Types
from ..catalog.upgrades import Upgrades
from ..dto.change import DROP_IN, Change, admits
from cryptobench.shared.catalogue.grouping import parse_qualified, provider_of
from cryptobench.shared.catalogue.key_types import build_key_types, entry_of
from ..dto.site import Scope
from cryptobench.shared.catalogue.types import TypeRow
from .change import Candidate, KeyTypes, classify


@dataclass(frozen=True)
class Family:
    """family_of and canonical_of by qualified item; bundled: the providers the app ships; min_sdk: the app's, None unknown."""
    family_of: dict[str, str]
    canonical_of: dict[str, str | None]
    types: Types
    min_sdk: int | None
    bundled: frozenset[str] = frozenset()
    max_change: str = DROP_IN
    upgrades: Upgrades | None = None

    def row(self, item: str) -> TypeRow | None:
        family = self.family_of.get(item)
        return self.types.of(family, self.canonical_of.get(item)) if family else None

    @cached_property
    def _key_types(self) -> dict[str, KeyTypes]:
        return {}

    def key_types(self, item: str) -> KeyTypes:
        """Read once per item: the key.types its provider's builds give it, empty without a catalogue entry; None: no type row."""
        if item not in self._key_types:
            engine_type, _, provider = parse_qualified(item)
            entry = entry_of(engine_type, self.canonical_of[item]) if self.row(item) is not None else None
            self._key_types[item] = None if self.row(item) is None else build_key_types(entry, provider) if entry is not None else frozenset()
        return self._key_types[item]

    def items(self, current: str, group: set[str]) -> list[str]:
        """Another canonical name in the current item's family, outside its group; the same name decided by grouping."""
        family, mine = self.family_of.get(current), self.canonical_of.get(current)
        if family is None:
            return []
        return sorted(q for q, f in self.family_of.items() if f == family and q != current and q not in group
                      and (mine is None or self.canonical_of.get(q) is None or fold(self.canonical_of[q]) != fold(mine)))

    def classed(self, s: Scope, current: str, group: set[str], measured, refused, foreign) -> list[Change]:
        """measured, refused, foreign (item): the run's facts the type catalog does not hold."""
        mine, keys = self.row(current), self.key_types(current)
        return [classify(self.types, s, mine, Candidate(q, self.row(q), measured(q), provider_of(q) in self.bundled,
                                                        refused(q), foreign(q)), self.min_sdk,
                         (keys, self.key_types(q)))
                for q in self.items(current, group)]

    def targets(self, current: str) -> frozenset[str]:
        """The upgrade list's folded target names for a broken current; empty when it is not listed."""
        return self.upgrades.targets(self.family_of.get(current), self.canonical_of.get(current)) if self.upgrades else frozenset()

    def split(self, changes: list[Change]) -> tuple[list[Change], list[Change]]:
        """(offered, not offered): a class up to maxChange is offered; a higher one is a recommendation, never applied."""
        offered = [c for c in changes if admits(self.max_change, c.change)]
        return offered, [c for c in changes if c not in offered]
