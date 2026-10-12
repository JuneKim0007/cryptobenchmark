"""Where the stage stands: the next item no record covers. Computed from the outbox, so it cannot drift;
cursor.json is written only so a person can see progress."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from ...dto.grouping import Item
from ...dto.grouping_state import OutboxRecord


@dataclass(frozen=True)
class Cursor:
    next: int | None
    assigned: int
    dropped: int
    knowledgeVersion: int

    def to_json(self) -> dict:
        return {"schemaVersion": 1, **asdict(self)}


def cursor(items: list[Item], records: list[OutboxRecord]) -> Cursor:
    decided = {r.item for r in records}
    remaining = [i.id for i in items if i.id not in decided]
    return Cursor(remaining[0] if remaining else None, sum(r.outcome == "assigned" for r in records),
                  sum(r.outcome == "dropped" for r in records), len(records))
