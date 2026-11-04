from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Reviews:
    """One result per reviewed family, the projection of the review outbox."""
    version: int = 0
    families: dict[str, dict] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"version": self.version, "families": self.families}
