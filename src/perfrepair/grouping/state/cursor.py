from __future__ import annotations

from dataclasses import asdict, dataclass

from ...dto.grouping import SCHEMA_VERSION, Item
from ...dto.decision import OutboxRecord


@dataclass(frozen=True)
class Cursor:
    next: int | None
    decided: int
    dropped: int
    knowledgeVersion: int

    def to_json(self) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, **asdict(self)}


def cursor(items: list[Item], records: list[OutboxRecord]) -> Cursor:
    decided = {r.item for r in records}
    remaining = [i.id for i in items if i.key not in decided]
    return Cursor(remaining[0] if remaining else None, sum(r.outcome == "decided" for r in records),
                  sum(r.outcome == "dropped" for r in records), len(records))
