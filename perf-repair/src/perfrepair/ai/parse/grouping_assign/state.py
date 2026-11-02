from __future__ import annotations

from dataclasses import asdict, dataclass

from ....dto.decision import OutboxRecord
from ....dto.grouping import SCHEMA_VERSION, Item
from ....dto.grouping_state import Answer, Group, Knowledge


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


def apply(knowledge: Knowledge, record: OutboxRecord, item: Item) -> None:
    if record.outcome == "dropped":
        knowledge.dropped.append(item.id)
    else:
        a = Answer.from_json(record.decision)
        if not a.joins:
            if a.newGroupId in knowledge.groups:
                raise ValueError(f"record {record.seq}: group {a.newGroupId} already exists")
            knowledge.groups[a.newGroupId] = Group(item.family, a.newGroupDescription)
        knowledge.groups[a.target].members.append(item.id)
        for amendment in a.amend:
            knowledge.groups[amendment.group].description = amendment.description
    knowledge.version += 1
