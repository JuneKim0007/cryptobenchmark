from __future__ import annotations

from ....dto.decision import OutboxRecord
from ....dto.grouping import Item, read_items, read_profiles
from ....dto.grouping_state import Knowledge
from ....dto.prompt import Charter, TaskPrompt
from ....dto.screen import Verdict, read_screen
from ....files import read_json, write_json
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from ....validation.parse.grouping_assign import MAX_DESCRIPTION, SLUG, parse_answer, validate_answer
from ....validation.grouping.code_groups import validate_code_groups
from ....validation.grouping.items import validate_items
from ....validation.grouping.knowledge import validate_knowledge
from ....catalog.families import Families
from ....run_dir import GroupingPaths
from ....screen.groups import charter_inputs, code_groups, screened_out
from .render import render
from .schema import SCHEMA
from .state import apply, cursor

NAME = "parse/grouping-assign"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs, id_pattern=SLUG.pattern, max_description=MAX_DESCRIPTION)


class GroupingKind:
    name = "grouping"
    schema = SCHEMA

    def __init__(self, paths: GroupingPaths, families: Families | None = None):
        self.paths, self.families = paths, families or Families.load()
        raw = read_json(paths.items)
        self._raw = {r["id"]: r for r in raw["items"]}
        self._items = read_items(raw)
        self.by_id = {i.id: i for i in self._items}
        self.profiles = read_profiles(read_json(paths.profiles))
        self.screen: dict[int, Verdict] | None = read_screen(read_json(paths.screen)) if paths.screen.exists() else None

    @property
    def inputs(self) -> str:
        return charter_inputs(self.screen)

    def items(self) -> list[Item]:
        return self._items

    def pending(self) -> list[Item]:
        return [i for i in self._items if not screened_out((self.screen or {}).get(i.id))]

    def empty(self) -> Knowledge:
        return Knowledge(groups=code_groups(self._items, self.screen))

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

    def render(self, item: Item, knowledge: Knowledge) -> TaskPrompt:
        return TaskPrompt(NAME, render(item, self.families.by_id[item.family], knowledge, self.by_id), item.key)

    def check(self, item: Item, text: str, knowledge: Knowledge) -> tuple[dict | None, list[str]]:
        answer, problems = parse_answer(text)
        problems = problems or validate_answer(answer, item, knowledge, self.families)
        return (None if problems else answer.to_json()), problems

    def apply(self, knowledge: Knowledge, item: Item, record: OutboxRecord) -> None:
        apply(knowledge, record, item)

    def validate(self, knowledge: Knowledge, records: list[OutboxRecord]) -> list[str]:
        problems = validate_items(self._items, self.profiles, self.families)
        problems += validate_knowledge(knowledge, self.by_id, self.families)
        problems += validate_code_groups(knowledge.groups, self.by_id, self.screen)
        asked = {i.key for i in self.pending()}
        problems += [f"record {r.seq}: item {r.item} is grouped by code, not asked; rerun assign"
                     for r in records if r.item not in asked]
        return problems + replay_problems(self, knowledge, records)

    def write(self, knowledge: Knowledge, records: list[OutboxRecord]) -> None:
        write_json(self.paths.knowledge, knowledge.to_json())
        write_json(self.paths.cursor, cursor(self.pending(), records).to_json())
