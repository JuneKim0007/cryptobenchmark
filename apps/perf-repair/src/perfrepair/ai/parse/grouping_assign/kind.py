from __future__ import annotations

from cryptobench.paths import GroupingTree
from cryptobench.catalogue.families import Families
from ....dto.decision import OutboxRecord
from cryptobench.catalogue.grouping import Item, read_items, read_profiles
from ....dto.grouping_state import Knowledge
from ....dto.prompt import Charter, TaskPrompt
from ....dto.screen import Verdict
from ....files import read_json
from ....probe.identified import identified
from ....run_dir import load_used
from ....screen.groups import code_groups, reserved_catalog_groups
from ....validation.grouping.code_groups import validate_code_groups
from ....validation.grouping.items import validate_items
from ....validation.grouping.knowledge import validate_knowledge
from ....validation.parse.grouping_assign import (
    MAX_DESCRIPTION,
    SLUG,
    parse_answer,
    validate_answer,
)
from ....validation.screen import read_checked_screen
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import apply, cursor

NAME = "parse/grouping-assign"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs, id_pattern=SLUG.pattern, max_description=MAX_DESCRIPTION)


class GroupingKind:
    name = "grouping"
    schema = SCHEMA

    def __init__(self, paths: GroupingTree, families: Families | None = None):
        self.paths, self.families = paths, families or Families.load()
        raw = read_json(paths.items)
        self._raw = {r["id"]: r for r in raw["items"]}
        self._items = read_items(raw)
        self.by_id = {i.id: i for i in self._items}
        self.profiles = read_profiles(read_json(paths.profiles))
        self.screen: dict[int, Verdict] | None = read_checked_screen(paths)
        self._askable = [i for i in self._items if not identified(i, self.screen)]
        self._asked = {i.key for i in self._askable}
        used = load_used(paths.root.parent)
        # used.json narrows what is asked, never what a record adds: an item outside it keeps its group
        self.scope = None if used is None else used.names

    def items(self) -> list[Item]:
        return self._items

    def gone(self, key: str) -> Item:
        return Item.from_key(key)

    def askable(self) -> list[Item]:
        return self._askable

    def pending(self) -> list[Item]:
        return self._askable if self.scope is None else [i for i in self._askable if i.qualified in self.scope]

    def not_used(self, records: list[OutboxRecord]) -> list[Item]:
        """Askable, outside used.json and never asked: left unasked, never dropped."""
        done = {r.item for r in records}
        return [i for i in self._askable if self.scope is not None and i.qualified not in self.scope and i.key not in done]

    def empty(self) -> Knowledge:
        groups = code_groups(self._items, self.screen, self.profiles)
        return Knowledge(groups=groups, retired=reserved_catalog_groups(groups) if self.screen is not None else {})

    def label(self, item: Item) -> str:
        return item.qualified

    def admit(self, item: Item) -> list[str]:
        try:
            popped = Item.from_json(self._raw[item.id])
        except (KeyError, TypeError, ValueError) as e:
            return [f"{item.id}: does not parse into Item: {e}"]
        return [p for p in (
            f"{item.id}: differs from the item the run was built with" if popped != item else "",
            f"{item.id}: family {popped.family!r} unknown" if popped.family not in self.families.by_id else "",
            f"{item.id}: no profile" if item.id not in self.profiles else "",
        ) if p]

    def render(self, item: Item, knowledge: Knowledge) -> TaskPrompt:
        return TaskPrompt(NAME, render(item, self.families.by_id[item.family], knowledge, self.by_id, self.profiles), item.key)

    def narrowed(self, item: Item, knowledge: Knowledge) -> TaskPrompt:
        return TaskPrompt(NAME, render(item, self.families.by_id[item.family], knowledge, self.by_id, self.profiles, exact=True),
                          item.key)

    def check(self, item: Item, text: str, knowledge: Knowledge) -> tuple[dict | None, list[str]]:
        answer, problems = parse_answer(text)
        problems = problems or validate_answer(answer, item, knowledge, self.families, self.profiles)
        return (None if problems else answer.to_json()), problems

    def apply(self, knowledge: Knowledge, item: Item, record: OutboxRecord) -> None:
        apply(knowledge, record, item, item.key in self._asked)

    def validate(self, knowledge: Knowledge, records: list[OutboxRecord]) -> list[str]:
        problems = validate_items(self._items, self.profiles, self.families)
        problems += validate_knowledge(knowledge, self.by_id, self.families)
        problems += validate_code_groups(knowledge.groups, self.by_id, self.screen, self.profiles)
        return problems + replay_problems(self, knowledge, records)

    def documents(self, knowledge: Knowledge, records: list[OutboxRecord]) -> dict:
        return {self.paths.knowledge: knowledge.to_json(), self.paths.cursor: cursor(self.pending(), records).to_json()}
