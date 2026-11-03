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


def apply(knowledge: Knowledge, record: OutboxRecord, item: Item, asked: bool = True) -> None:
    """asked False: the item left, or is screened out now; its record still names groups, it adds no member."""
    if record.outcome == "dropped":
        if asked:
            knowledge.dropped.append(item.id)
    else:
        a = Answer.from_json(record.decision)
        if not a.joins:
            if knowledge.taken(a.newGroupId):
                raise ValueError(f"record {record.seq}: group {a.newGroupId} already exists")
            knowledge.retired[a.newGroupId] = Group(item.family, a.newGroupDescription)
        if asked:
            knowledge.filled(a.target).members.append(item.id)
        for amendment in a.amend:
            knowledge.held(amendment.group).description = amendment.description
    knowledge.version += 1
