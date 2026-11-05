"""The upgrade decision's state: what each broken use became, and its version."""
from __future__ import annotations

from dataclasses import dataclass, field

from ....dto.upgrade import SCHEMA_VERSION, Upgrade


@dataclass
class UpgradeState:
    app: str
    version: int = 0
    rows: dict[str, Upgrade] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "app": self.app,
                "upgrades": [self.rows[s].to_json() for s in sorted(self.rows)]}
