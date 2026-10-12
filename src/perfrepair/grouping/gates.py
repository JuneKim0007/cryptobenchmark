"""The checks the loop runs around every item; each raises ValidationFailed naming every problem.

  A  before pop:   items and profiles valid, outbox readable and contiguous, knowledge == replay(outbox)
  B  after pop:    the item parses whole, carries no group, its family and profile exist
  D  after write:  the written record reads back equal, and the new knowledge validates
"""
from __future__ import annotations

from ..dto.grouping import Item, Profile
from ..dto.grouping_state import Knowledge, OutboxRecord
from ..validation import require
from ..validation.grouping.items import validate_items
from ..validation.grouping.knowledge import validate_knowledge
from .catalog.families import Families


def before_pop(items: list[Item], profiles: dict[int, Profile], records: list[OutboxRecord],
               knowledge: Knowledge, families: Families) -> None:
    require("items", validate_items(items, profiles, families))
    require("knowledge", validate_knowledge(knowledge, records, {i.id: i for i in items}, families))


def after_pop(raw: dict, profiles: dict[int, Profile], families: Families) -> Item:
    try:
        item = Item.from_json(raw)
    except (KeyError, TypeError, ValueError) as e:
        require("popped item", [f"does not parse into Item: {e}"])
    require("popped item", [p for p in (
        f"{item.id}: carries group {item.group!r}" if item.group is not None else "",
        f"{item.id}: family {item.family!r} unknown" if item.family not in families.by_id else "",
        f"{item.id}: no profile" if item.id not in profiles else "",
    ) if p])
    return item


def after_write(written: OutboxRecord, read_back: OutboxRecord, records: list[OutboxRecord], knowledge: Knowledge,
                items: list[Item], families: Families) -> None:
    require("outbox record", [] if written == read_back else [f"record {written.seq} reads back different"])
    require("knowledge", validate_knowledge(knowledge, records, {i.id: i for i in items}, families))
