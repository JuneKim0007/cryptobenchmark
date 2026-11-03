from __future__ import annotations

from dataclasses import dataclass

KNOWN, CONVENTION, UNKNOWN = "known", "convention", "unknown"


@dataclass(frozen=True)
class Component:
    """known: read from this item's name, resolved or key contract; convention: a provider's habit, assumed;
    unknown: nothing recorded, value None, never the name's default."""
    name: str
    value: str | None
    status: str = KNOWN


@dataclass(frozen=True)
class Signature:
    components: tuple[Component, ...]

    @property
    def decided(self) -> bool:
        return all(c.status != UNKNOWN for c in self.components)

    @property
    def assumed(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.components if c.status == CONVENTION)

    @property
    def identity(self) -> tuple[tuple[str, str | None], ...]:
        return tuple((c.name, c.value) for c in self.components)

    def known(self) -> dict[str, str]:
        return {c.name: c.value for c in self.components if c.status == KNOWN}

    def differing(self, other: "Signature") -> list[str]:
        """Components both know and disagree on; an unknown or assumed one decides nothing."""
        mine, theirs = self.known(), other.known()
        return sorted(n for n in mine.keys() & theirs.keys() if mine[n] != theirs[n])

    def to_json(self) -> dict:
        return {"components": [{"name": c.name, "value": c.value, "status": c.status} for c in self.components]}

    @classmethod
    def from_json(cls, d: dict) -> "Signature":
        return cls(tuple(Component(c["name"], c["value"], c["status"]) for c in d["components"]))
