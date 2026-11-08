"""Tier: one model choice a job asks at; the settings resolve to one, escalation steps to the next."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Tier:
    gateway: str
    model: str | None = None
    effort: str | None = None
    webSearch: bool = False

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "Tier":
        return cls(d["gateway"], d.get("model"), d.get("effort"), bool(d.get("webSearch")))

    def __str__(self) -> str:
        return f"{self.gateway}/{self.model}/{self.effort}" + ("/web" if self.webSearch else "")


@dataclass(frozen=True)
class Ladder:
    """A gateway's models, weakest first: the order escalation climbs."""
    models: tuple[str, ...] = ()
