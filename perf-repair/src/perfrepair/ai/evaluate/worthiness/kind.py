from __future__ import annotations

from pathlib import Path

from .... import run_dir as rd
from ....dto import GroupEvidence, Verdict, Verdicts
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....files import write_json
from ....result.modes import Mode
from ....result.triage import triage
from ....validation.evaluate.worthiness import check_reply
from ....validation.worthiness import validate_verdicts
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA

NAME = "evaluate/worthiness"


def charter(library: PromptLibrary) -> Charter:
    return library.charter(NAME, SCHEMA)


class WorthinessKind:

    def __init__(self, mode: Mode, comparability: list[str], evidence: list[GroupEvidence], directory: Path):
        self.mode, self.comparability, self.evidence, self.directory = mode, comparability, evidence, Path(directory)
        self.name = f"worthiness-{mode.name}"
        self._ask, self.static = triage(evidence, mode)

    def items(self) -> list[GroupEvidence]:
        return self._ask

    def empty(self) -> Verdicts:
        return Verdicts(self.mode.name, 0, {v.groupId: v for v in self.static})

    def admit(self, e: GroupEvidence) -> list[str]:
        return []

    def label(self, e: GroupEvidence) -> str:
        return e.groupId

    def render(self, e: GroupEvidence, verdicts: Verdicts) -> TaskPrompt:
        return TaskPrompt(NAME, render(e, self.mode, self.comparability), e.key)

    def check(self, e: GroupEvidence, text: str, verdicts: Verdicts) -> tuple[dict | None, list[str]]:
        return check_reply(text, e, self.mode)

    def apply(self, verdicts: Verdicts, e: GroupEvidence, record: OutboxRecord) -> None:
        verdicts.verdicts[e.groupId] = (Verdict.from_json(record.decision) if record.outcome == "decided" else
                                        Verdict(e.groupId, self.mode.name, "skip", "dropped: " + "; ".join(record.problems),
                                                "fallback", self.mode.proxy))
        verdicts.version += 1

    def validate(self, verdicts: Verdicts, records: list[OutboxRecord]) -> list[str]:
        return validate_verdicts(verdicts, self.evidence, self.mode) + replay_problems(self, verdicts, records)

    def write(self, verdicts: Verdicts, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.VERDICTS, verdicts.to_json())
