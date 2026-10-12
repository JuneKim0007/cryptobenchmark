"""Grouping as a decision kind on the engine: one primitive per item, placed into a group of its family.

Gate A (validate): items and profiles valid, knowledge well-formed and equal to the replay of the outbox.
Gate B (admit): the popped item, re-read from items.json, parses whole and carries no group.
Gate C (check): parse_answer + validate_answer.
"""
from __future__ import annotations

from ..dto.decision import OutboxRecord
from ..dto.grouping import Item, read_items, read_profiles
from ..dto.grouping_state import Knowledge
from ..files import read_json, write_json
from ..orchestrate.engine.kind import project
from ..validation.grouping.answer import parse_answer, validate_answer
from ..validation.grouping.items import validate_items
from ..validation.grouping.knowledge import validate_knowledge
from .catalog.families import Families
from .paths import GroupingPaths
from .prompt.render import render, system_prompt
from .prompt.schema import SCHEMA
from .state.cursor import cursor
from .state.knowledge import apply


class GroupingKind:
    name = "grouping"
    schema = SCHEMA

    def __init__(self, paths: GroupingPaths, families: Families | None = None):
        self.paths, self.families = paths, families or Families.load()
        self.system = system_prompt()
        raw = read_json(paths.items)
        self._raw = {r["id"]: r for r in raw["items"]}
        self._items = read_items(raw)
        self.by_id = {i.id: i for i in self._items}
        self.profiles = read_profiles(read_json(paths.profiles))

    def items(self) -> list[Item]:
        return self._items

    def empty(self) -> Knowledge:
        return Knowledge()

    def label(self, item: Item) -> str:
        return item.qualified

    def admit(self, item: Item) -> list[str]:
        try:
            popped = Item.from_json(self._raw[item.id])
        except (KeyError, TypeError, ValueError) as e:
            return [f"{item.id}: does not parse into Item: {e}"]
        return [p for p in (
            f"{item.id}: differs from the item the run was built with" if popped != item else "",
            f"{item.id}: carries group {popped.group!r}" if popped.group is not None else "",
            f"{item.id}: family {popped.family!r} unknown" if popped.family not in self.families.by_id else "",
            f"{item.id}: no profile" if item.id not in self.profiles else "",
        ) if p]

    def render(self, item: Item, knowledge: Knowledge) -> str:
        return render(item, self.families.by_id[item.family], knowledge, self.by_id)

    def check(self, item: Item, text: str, knowledge: Knowledge) -> tuple[dict | None, list[str]]:
        answer, problems = parse_answer(text)
        problems = problems or validate_answer(answer, item, knowledge, self.families)
        return (None if problems else answer.to_json()), problems

    def apply(self, knowledge: Knowledge, item: Item, record: OutboxRecord) -> None:
        apply(knowledge, record, item)

    def validate(self, knowledge: Knowledge, records: list[OutboxRecord]) -> list[str]:
        problems = validate_items(self._items, self.profiles, self.families)
        problems += validate_knowledge(knowledge, self.by_id, self.families)
        if knowledge.version != len(records):
            problems.append(f"knowledge version {knowledge.version} is not the {len(records)} records committed")
        try:
            if project(self, records).to_json() != knowledge.to_json():
                problems.append("knowledge differs from the replay of the outbox")
        except (KeyError, ValueError) as e:
            problems.append(f"outbox does not replay: {e}")
        return problems

    def write(self, knowledge: Knowledge, records: list[OutboxRecord]) -> None:
        write_json(self.paths.knowledge, knowledge.to_json())
        write_json(self.paths.cursor, cursor(self._items, records).to_json())
