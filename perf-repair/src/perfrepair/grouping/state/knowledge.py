from __future__ import annotations

from ...dto.decision import OutboxRecord
from ...dto.grouping import Item
from ...dto.grouping_state import Answer, Group, Knowledge


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
