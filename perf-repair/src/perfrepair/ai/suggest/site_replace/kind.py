from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .... import run_dir as rd
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....dto.site import Replacement
from ....dto.unit import UnitDossiers
from ....files import json_text, sha256_text, write_json
from ....validation.dossiers import check_dossier
from ....validation.dossiers import parse_dossiers
from ....validation.suggest.site_replace import check_reply
from ....validation.replacements import validate_replacements, whole_units
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
    """A record's unit that is not asked any more: its record adds no row."""
    key: str


def evidence(u: UnitDossiers) -> str:
    return sha256_text(json_text({"unit": u.unit.to_json(), "dossiers": [d.to_json() for d in u.dossiers]}))


class SiteReplaceKind:
    name = "site-replace"

    def __init__(self, app: str, doc: dict, directory: Path):
        self.app, self.doc, self.directory = app, doc, Path(directory)
        self.units, self.no_options, self.problems = parse_dossiers(doc, app)

    def items(self) -> list[UnitDossiers]:
        return self.units

    def pending(self) -> list[UnitDossiers]:
        return self.items()

    def gone(self, key: str) -> Gone:
        return Gone(key)

    def evidence_digest(self, u: UnitDossiers) -> str:
        return evidence(u)

    def empty(self) -> Replacements:
        state = Replacements(self.app)
        for scope, reason in self.no_options.items():
            state.put(Replacement(scope, "keep", None, (), (), reason), "static")
        return state

    def admit(self, u: UnitDossiers) -> list[str]:
        raws = {(r.get("scope") or {}).get("id"): r for r in self.doc.get("dossiers") or []}
        problems = []
        for d in u.dossiers:
            popped, found = check_dossier(raws.get(d.key), self.app)
            problems += found + ([f"{d.key}: differs from the dossier the run was built with"] if popped != d else [])
        return problems

    def label(self, u: UnitDossiers | Gone) -> str:
        if isinstance(u, Gone):
            return f"{u.key} (gone)"
        first = u.dossiers[0].scope
        return f"{first.file}:{first.line}" + (f" +{len(u.dossiers) - 1}" if len(u.dossiers) > 1 else "")

    def render(self, u: UnitDossiers, state: Replacements) -> TaskPrompt:
        return TaskPrompt(NAME, render(u), u.key)

    def check(self, u: UnitDossiers, text: str, state: Replacements) -> tuple[dict | None, list[str]]:
        return check_reply(text, u)

    def apply(self, state: Replacements, u: UnitDossiers | Gone, record: OutboxRecord) -> None:
        state.version += 1
        if isinstance(u, Gone):
            return
        # a record without evidence predates it and cannot be shown to match
        mark = state.stale.add if record.evidence != evidence(u) else state.stale.discard
        for member in u.unit.members:
            mark(member)
        if record.outcome == "decided":
            for row in record.decision["replacements"]:
                state.put(Replacement.from_json(row), "llm")
            return
        for member in u.unit.members:
            state.put(Replacement(member, "keep", None, (), (), "dropped: " + "; ".join(record.problems)), "fallback")

    def validate(self, state: Replacements, records: list[OutboxRecord]) -> list[str]:
        dossiers = [d for u in self.units for d in u.dossiers]
        problems = list(self.problems) + validate_replacements(state.replacements, state.sources, dossiers,
                                                                self.no_options, state.stale)
        return problems + whole_units(state.replacements, self.units) + replay_problems(self, state, records)

    def write(self, state: Replacements, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.REPLACEMENTS, state.to_json())
