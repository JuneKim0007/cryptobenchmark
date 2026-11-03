"""A scope's candidates outside its current item's group: the items of its family under another canonical name, each
classed against the current type; those up to maxChange are offered, the others kept with their class or reasons."""
from __future__ import annotations

from dataclasses import dataclass

from ..catalog.names import fold
from ..catalog.types import Types
from ..dto.change import DROP_IN, Change, admits
from ..dto.site import Scope
from ..dto.types import TypeRow
from .change import Candidate, classify


@dataclass(frozen=True)
class Family:
    """family_of and canonical_of by qualified item; bundled: the providers the app ships; min_sdk: the app's, None unknown."""
    family_of: dict[str, str]
    canonical_of: dict[str, str | None]
    types: Types
    min_sdk: int | None
    bundled: frozenset[str] = frozenset()
    max_change: str = DROP_IN

    def row(self, item: str) -> TypeRow | None:
        family = self.family_of.get(item)
        return self.types.of(family, self.canonical_of.get(item)) if family else None

    def items(self, current: str, group: set[str]) -> list[str]:
        """Another canonical name in the current item's family, outside its group; the same name decided by grouping."""
        family, mine = self.family_of.get(current), self.canonical_of.get(current)
        if family is None:
            return []
        return sorted(q for q, f in self.family_of.items() if f == family and q != current and q not in group
                      and (mine is None or self.canonical_of.get(q) is None or fold(self.canonical_of[q]) != fold(mine)))

    def classed(self, s: Scope, current: str, group: set[str], provider_of, measured, lowers, foreign) -> list[Change]:
        """measured, lowers, foreign (item): the run's facts the type catalog does not hold."""
        mine = self.row(current)
        return [classify(self.types, s, mine, Candidate(q, self.row(q), measured(q), provider_of(q) in self.bundled,
                                                        lowers(q), foreign(q)), self.min_sdk)
                for q in self.items(current, group)]

    def split(self, changes: list[Change]) -> tuple[list[Change], list[Change]]:
        """(offered, not offered): a class up to maxChange is offered; a higher one is a recommendation, never applied."""
        offered = [c for c in changes if admits(self.max_change, c.change)]
        return offered, [c for c in changes if c not in offered]
