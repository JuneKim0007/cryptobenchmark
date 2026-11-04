"""The replacement decision's state: one Replacement per scope, where each came from, the ones decided on an earlier
dossier, and its version."""
from __future__ import annotations

from dataclasses import dataclass, field

from ....dto.replacement import Replacement
from ....dto.site import REPLACEMENTS_SCHEMA_VERSION


@dataclass
class Replacements:
    app: str
    version: int = 0
    replacements: dict[str, Replacement] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    stale: set[str] = field(default_factory=set)

    def put(self, r: Replacement, source: str) -> None:
        self.replacements[r.scope], self.sources[r.scope] = r, source

    def to_json(self) -> dict:
        return {"schemaVersion": REPLACEMENTS_SCHEMA_VERSION, "app": self.app,
                "replacements": [r.to_json() for r in self.replacements.values()],
                "sources": dict(self.sources), "stale": sorted(self.stale)}
