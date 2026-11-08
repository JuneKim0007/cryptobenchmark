"""upgrades.json as Select's upgrade state: what each broken use became."""
from __future__ import annotations

from dataclasses import dataclass, field

from ...dto.upgrade import SCHEMA_VERSION, Upgrade


@dataclass
class UpgradeState:
    app: str
    rows: dict[str, Upgrade] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "app": self.app,
                "upgrades": [self.rows[s].to_json() for s in sorted(self.rows)]}
