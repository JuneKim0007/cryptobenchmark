from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .... import run_dir as rd
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....dto.site import Dossier, Replacement
from ....files import json_text, sha256_text, write_json
from ....validation.dossiers import check_dossier
from ....validation.dossiers import parse_dossiers
from ....validation.suggest.site_replace import check_reply
from ....validation.replacements import validate_replacements
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import Replacements

NAME = "suggest/site-replace"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs)


@dataclass(frozen=True)
class Gone:
    """A record's scope that has no dossier any more: its record adds no row."""
    key: str


def evidence(d: Dossier) -> str:
    return sha256_text(json_text(d.to_json()))


class SiteReplaceKind:
    name = "site-replace"

    def __init__(self, app: str, doc: dict, directory: Path):
        self.app, self.doc, self.directory = app, doc, Path(directory)
        self.dossiers, self.no_options, self.problems = parse_dossiers(doc, app)

    def items(self) -> list[Dossier]:
        return self.dossiers

    def pending(self) -> list[Dossier]:
        return self.items()

    def gone(self, key: str) -> Gone:
        return Gone(key)

    def evidence_digest(self, d: Dossier) -> str:
        return evidence(d)

    def empty(self) -> Replacements:
        state = Replacements(self.app)
        for scope, reason in self.no_options.items():
            state.put(Replacement(scope, "keep", None, (), (), reason), "static")
        return state

    def admit(self, d: Dossier) -> list[str]:
        raw = next((r for r in self.doc.get("dossiers") or [] if (r.get("scope") or {}).get("id") == d.key), None)
        popped, problems = check_dossier(raw, self.app)
        return (["differs from the dossier the run was built with"] if popped != d else []) + problems

    def label(self, d: Dossier | Gone) -> str:
        return f"{d.key} (gone)" if isinstance(d, Gone) else f"{d.scope.file}:{d.scope.line}"

    def render(self, d: Dossier, state: Replacements) -> TaskPrompt:
        return TaskPrompt(NAME, render(d), d.key)

    def check(self, d: Dossier, text: str, state: Replacements) -> tuple[dict | None, list[str]]:
        return check_reply(text, d)

    def apply(self, state: Replacements, d: Dossier | Gone, record: OutboxRecord) -> None:
        if isinstance(d, Gone):
            state.version += 1
            return
        # a record without evidence predates it and cannot be shown to match
        (state.stale.add if record.evidence != evidence(d) else state.stale.discard)(d.key)
        if record.outcome == "decided":
            state.put(Replacement.from_json(record.decision), "llm")
        else:
            state.put(Replacement(d.key, "keep", None, (), (), "dropped: " + "; ".join(record.problems)), "fallback")
        state.version += 1

    def validate(self, state: Replacements, records: list[OutboxRecord]) -> list[str]:
        problems = list(self.problems) + validate_replacements(state.replacements, state.sources, self.dossiers,
                                                                    self.no_options, state.stale)
        return problems + replay_problems(self, state, records)

    def write(self, state: Replacements, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.REPLACEMENTS, state.to_json())
