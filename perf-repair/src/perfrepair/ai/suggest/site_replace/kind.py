from __future__ import annotations

from pathlib import Path

from .... import run_dir as rd
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....dto.site import Dossier, Replacement
from ....files import write_json
from ....validation.dossiers import check_dossier
from ....validation.suggest.dossier import parse_dossiers
from ....validation.suggest.replace import check_reply
from ....validation.suggest.replacements import validate_replacements
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import Replacements

NAME = "suggest/site-replace"


def charter(library: PromptLibrary) -> Charter:
    return library.charter(NAME, SCHEMA)


class SiteReplaceKind:
    name = "site-replace"

    def __init__(self, app: str, doc: dict, directory: Path):
        self.app, self.doc, self.directory = app, doc, Path(directory)
        self.dossiers, self.no_options, self.problems = parse_dossiers(doc, app)

    def items(self) -> list[Dossier]:
        return self.dossiers

    def empty(self) -> Replacements:
        state = Replacements(self.app)
        for scope, reason in self.no_options.items():
            state.put(Replacement(scope, "keep", None, (), (), reason), "static")
        return state

    def admit(self, d: Dossier) -> list[str]:
        raw = next((r for r in self.doc.get("dossiers") or [] if (r.get("scope") or {}).get("id") == d.key), None)
        popped, problems = check_dossier(raw, self.app)
        return (["differs from the dossier the run was built with"] if popped != d else []) + problems

    def label(self, d: Dossier) -> str:
        return f"{d.scope.file}:{d.scope.line}"

    def render(self, d: Dossier, state: Replacements) -> TaskPrompt:
        return TaskPrompt(NAME, render(d), d.key)

    def check(self, d: Dossier, text: str, state: Replacements) -> tuple[dict | None, list[str]]:
        return check_reply(text, d)

    def apply(self, state: Replacements, d: Dossier, record: OutboxRecord) -> None:
        if record.outcome == "decided":
            state.put(Replacement.from_json(record.decision), "llm")
        else:
            state.put(Replacement(d.key, "keep", None, (), (), "dropped: " + "; ".join(record.problems)), "fallback")
        state.version += 1

    def validate(self, state: Replacements, records: list[OutboxRecord]) -> list[str]:
        problems = list(self.problems) + validate_replacements(state.replacements, state.sources, self.dossiers,
                                                                    self.no_options)
        return problems + replay_problems(self, state, records)

    def write(self, state: Replacements, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.REPLACEMENTS, state.to_json())
