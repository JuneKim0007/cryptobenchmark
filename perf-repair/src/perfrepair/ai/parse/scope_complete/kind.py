from __future__ import annotations

from pathlib import Path

from .... import run_dir as rd
from ....dto.decision import OutboxRecord
from ....dto.gaps import ScopeGaps
from ....dto.prompt import Charter, TaskPrompt
from ....files import json_text, sha256_text, write_json
from ....validation.completed import validate_completed
from ....validation.parse.scope_complete import check_reply
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import Completed, apply

NAME = "parse/scope-complete"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs)


def _key_first(e: ScopeGaps) -> tuple:
    # a capped run spends its calls on the scopes whose key provenance is open
    return (not any(g.name == "key" for g in e.offered), e.file, e.anchor.line, e.scope)


class ScopeCompleteKind:
    name = "scope-complete"
    schema = SCHEMA

    def __init__(self, app: str, entries: list[ScopeGaps], directory: Path):
        self.app, self.entries, self.directory = app, entries, Path(directory)

    @property
    def inputs(self) -> str:
        """The whole evidence: another gap or candidate starts a new outbox, a reverted one resumes."""
        return sha256_text(json_text([e.to_json() for e in self.entries]))

    def items(self) -> list[ScopeGaps]:
        return sorted((e for e in self.entries if e.offered), key=_key_first)

    def pending(self) -> list[ScopeGaps]:
        return self.items()

    def empty(self) -> Completed:
        return Completed(self.app)

    def admit(self, e: ScopeGaps) -> list[str]:
        return [] if e.offered else ["no gap has a candidate"]

    def label(self, e: ScopeGaps) -> str:
        return f"{e.file}:{e.anchor.line}"

    def render(self, e: ScopeGaps, state: Completed) -> TaskPrompt:
        return TaskPrompt(NAME, render(e), e.key)

    def check(self, e: ScopeGaps, text: str, state: Completed) -> tuple[dict | None, list[str]]:
        return check_reply(text, e)

    def apply(self, state: Completed, e: ScopeGaps, record: OutboxRecord) -> None:
        apply(state, e, record)

    def validate(self, state: Completed, records: list[OutboxRecord]) -> list[str]:
        return validate_completed(state.answers, self.entries) + replay_problems(self, state, records)

    def write(self, state: Completed, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.COMPLETED, state.to_json())
