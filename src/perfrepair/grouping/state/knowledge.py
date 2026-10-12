"""Knowledge as a pure projection of the outbox: replay every record in order. Nothing edits it directly."""
from __future__ import annotations

from ...dto.grouping import Item
from ...dto.grouping_state import Group, Knowledge, OutboxRecord


def project(records: list[OutboxRecord], items: dict[int, Item]) -> Knowledge:
    knowledge = Knowledge()
    for r in records:
        apply(knowledge, r, items[r.item])
    return knowledge


def apply(knowledge: Knowledge, record: OutboxRecord, item: Item) -> None:
    """One record's effect; records are validated before they are written, so a failure here is corruption."""
    if record.outcome == "dropped":
        knowledge.dropped.append(record.item)
    else:
        a = record.answer
        if not a.joins:
            if a.newGroupId in knowledge.groups:
                raise ValueError(f"record {record.seq}: group {a.newGroupId} already exists")
            knowledge.groups[a.newGroupId] = Group(item.family, a.newGroupDescription)
        knowledge.groups[a.target].members.append(record.item)
        for amendment in a.amend:
            knowledge.groups[amendment.group].description = amendment.description
    knowledge.version += 1
