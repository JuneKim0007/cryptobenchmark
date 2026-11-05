from __future__ import annotations

from dataclasses import dataclass

from ....catalog.groups import group_catalog
from ....dto.decision import OutboxRecord
from ....dto.grouping import read_items, read_profiles
from ....dto.grouping_state import code_made
from ....dto.prompt import Charter, TaskPrompt
from ....files import read_json, sha256_text
from ....run_dir import GroupingPaths
from ....screen.groups import identified
from ....validation.grouping.output import read_groups
from ....validation.review.grouping_review import parse_review
from ....validation.screen import read_checked_screen
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import Reviews

SCHEMA_VERSION = 2
NAME = "review/grouping-review"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs)


@dataclass(frozen=True)
class Family:
    key: str
    text: str
    membership: dict[str, list[int]]


def _model_decided(paths: GroupingPaths):
    """A catalog group holding only what the catalog placed has no model decision to review; code-made groups neither."""
    screen = read_checked_screen(paths)
    items = {i.id: i for i in read_items(read_json(paths.items))}
    profiles = read_profiles(read_json(paths.profiles))

    def decided(group: dict) -> bool:
        if code_made(group["id"]):
            return False
        return group_catalog().variant_of(group["id"]) is None or any(
            not identified(items[m], screen, profiles) for m in group["members"])
    return decided


def _families(paths: GroupingPaths) -> list[Family]:
    document, checks = read_groups(paths), read_json(paths.checks)
    decided = _model_decided(paths)
    found = []
    for name in sorted(document["families"]):
        groups = [g for g in document["groups"] if g["family"] == name and decided(g)]
        if groups:
            text = render(name, document["families"][name], groups, document["items"], checks["findings"])
            found.append(Family(name, text, {g["id"]: g["members"] for g in groups}))
    return found


class GroupingReviewKind:
    name = "supervisor"
    schema = SCHEMA

    def __init__(self, paths: GroupingPaths, library: PromptLibrary | None = None, saved: dict | None = None):
        """library: what a run writes with; saved: the document a replay rebuilds, its charter and prompts as recorded."""
        self.paths, self.families, saved = paths, _families(paths), saved or {}
        self.charter = charter(library, self.inputs) if library else None
        self.fingerprint = self.charter.fingerprint if library else saved.get("charter")
        self.prompts = library.provenance(self.charter) if library else saved.get("prompts", {})

    @property
    def inputs(self) -> str:
        """The messages: other groups start a new outbox, reverted ones resume."""
        return "reviewed " + sha256_text("\0".join(f"{f.key}\0{f.text}" for f in self.families))

    def items(self) -> list[Family]:
        return self.families

    def pending(self) -> list[Family]:
        return self.families

    def empty(self) -> Reviews:
        return Reviews()

    def admit(self, family: Family) -> list[str]:
        return [] if family.membership else [f"{family.key}: no group to review"]

    def label(self, family: Family) -> str:
        return family.key

    def render(self, family: Family, state: Reviews) -> TaskPrompt:
        return TaskPrompt(NAME, family.text, family.key)

    def check(self, family: Family, text: str, state: Reviews) -> tuple[dict | None, list[str]]:
        findings, problems = parse_review(text, family.membership)
        return (None if findings is None else {"findings": findings}), problems

    def apply(self, state: Reviews, family: Family, record: OutboxRecord) -> None:
        state.families[family.key] = ({"status": "reviewed", "findings": record.decision["findings"], "problems": []}
                                      if record.outcome == "decided" else
                                      {"status": "failed", "findings": [], "problems": list(record.problems)})
        state.version += 1

    def validate(self, state: Reviews, records: list[OutboxRecord]) -> list[str]:
        return replay_problems(self, state, records)

    def document(self, state: Reviews) -> dict:
        return {"schemaVersion": SCHEMA_VERSION, "charter": self.fingerprint, "prompts": self.prompts,
                "families": state.families}

    def documents(self, state: Reviews, records: list[OutboxRecord]) -> dict:
        return {self.paths.supervisor: self.document(state)}
