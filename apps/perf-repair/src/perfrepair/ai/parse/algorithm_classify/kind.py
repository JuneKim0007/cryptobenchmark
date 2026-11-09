from __future__ import annotations

import json

from cryptobench.paths import GroupingTree
from ....dto.classify import Batch
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....validation.classified import validate_classified
from ....validation.parse.algorithm_classify import check_reply
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import Classified, apply

NAME = "parse/algorithm-classify"


def charter(library: PromptLibrary, inputs: str) -> Charter:
    return library.charter(NAME, SCHEMA, inputs)


class ClassifyKind:
    name = "classify"
    schema = SCHEMA

    def __init__(self, batches: list[Batch], paths: GroupingTree):
        self.batches, self.paths = batches, paths

    @property
    def inputs(self) -> str:
        """The whole evidence: another unknown set or other evidence starts a new outbox, a reverted one resumes."""
        return json.dumps([[e.to_json() for e in b.members] for b in self.batches], sort_keys=True)

    def items(self) -> list[Batch]:
        return self.batches

    def pending(self) -> list[Batch]:
        return self.batches

    def empty(self) -> Classified:
        return Classified()

    def admit(self, batch: Batch) -> list[str]:
        return [] if batch.members else ["empty batch"]

    def label(self, batch: Batch) -> str:
        return f"items {batch.key}"

    def render(self, batch: Batch, state: Classified) -> TaskPrompt:
        return TaskPrompt(NAME, render(batch), batch.key)

    def check(self, batch: Batch, text: str, state: Classified) -> tuple[dict | None, list[str]]:
        return check_reply(text, batch)

    def apply(self, state: Classified, batch: Batch, record: OutboxRecord) -> None:
        apply(state, batch, record)

    def validate(self, state: Classified, records: list[OutboxRecord]) -> list[str]:
        return validate_classified(state.answers, self.batches) + replay_problems(self, state, records)

    def documents(self, state: Classified, records: list[OutboxRecord]) -> dict:
        return {self.paths.classified: state.to_json()}
