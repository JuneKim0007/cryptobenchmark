from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .... import run_dir as rd
from ....dto.change import DROP_IN
from ....dto.decision import OutboxRecord
from ....dto.prompt import Charter, TaskPrompt
from ....dto.perf_mode import PerfMode
from ....dto.primitives import PrimitivesTable
from ....dto.site import Replacement
from ....dto.unit import UnitDossiers
from ....dto.units import DisplayUnits
from ....files import json_text, sha256_text, write_json
from ....validation.dossiers import check_dossier, parse_dossiers, perf_of
from ....validation.suggest.site_replace import check_reply
from ....validation.replacements import consistent_units, validate_replacements
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .rows import digest_input
from .schema import SCHEMA
from .state import Replacements

NAME = "suggest/site-replace"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs)


@dataclass(frozen=True)
class Gone:
    """A record's unit that is not asked any more: its record adds no row."""
    key: str


def evidence(u: UnitDossiers, perf: PerfMode, table: PrimitivesTable | None = None) -> str:
    """The selection and the primitives.tsv lines shown are evidence too: a change in either marks the decision stale."""
    shown = {"lines": [digest_input(d, table) for d in u.dossiers]} if table is not None else {}
    return sha256_text(json_text({"unit": u.entry(), "dossiers": [d.to_json() for d in u.dossiers], "perfMode": perf.to_json(),
                                  **shown}))


class SiteReplaceKind:
    name = "site-replace"

    def __init__(self, app: str, doc: dict, directory: Path, table: PrimitivesTable | None = None,
                 units: DisplayUnits = DisplayUnits()):
        """table: the device's primitives.tsv, shown beside the estimates; units: the manifest's display units."""
        self.app, self.doc, self.directory, self.table, self.display = app, doc, Path(directory), table, units
        self.units, self.no_options, self.problems = parse_dossiers(doc, app)
        self.perf = perf_of(doc) or PerfMode()
        self.max_change = doc.get("maxChange", DROP_IN)

    def items(self) -> list[UnitDossiers]:
        return self.units

    def pending(self) -> list[UnitDossiers]:
        return self.items()

    def gone(self, key: str) -> Gone:
        return Gone(key)

    def evidence_digest(self, u: UnitDossiers) -> str:
        return evidence(u, self.perf, self.table)

    def empty(self) -> Replacements:
        state = Replacements(self.app)
        for scope, reason in self.no_options.items():
            state.put(Replacement(scope, "keep", None, (), (), reason), "static")
        return state

    def admit(self, u: UnitDossiers) -> list[str]:
        raws = {(r.get("scope") or {}).get("id"): r for r in self.doc.get("dossiers") or []}
        problems = []
        for d in u.dossiers:
            popped, found = check_dossier(raws.get(d.key), self.app, self.perf, self.max_change)
            problems += found + ([f"{d.key}: differs from the dossier the run was built with"] if popped != d else [])
        return problems

    def label(self, u: UnitDossiers | Gone) -> str:
        if isinstance(u, Gone):
            return f"{u.key} (gone)"
        first = u.dossiers[0].scope
        return f"{first.file}:{first.line}" + (f" +{len(u.dossiers) - 1}" if len(u.dossiers) > 1 else "")

    def render(self, u: UnitDossiers, state: Replacements) -> TaskPrompt:
        return TaskPrompt(NAME, render(u, self.perf, self.table, self.display), u.key)

    def check(self, u: UnitDossiers, text: str, state: Replacements) -> tuple[dict | None, list[str]]:
        return check_reply(text, u, self.max_change)

    def apply(self, state: Replacements, u: UnitDossiers | Gone, record: OutboxRecord) -> None:
        state.version += 1
        if isinstance(u, Gone):
            return
        # a record without evidence predates it and cannot be shown to match
        mark = state.stale.add if record.evidence != evidence(u, self.perf, self.table) else state.stale.discard
        for d in u.dossiers:
            mark(d.key)
        if record.outcome == "decided":
            for row in record.decision["replacements"]:
                state.put(Replacement.from_json(row), "llm")
            return
        for d in u.dossiers:
            state.put(Replacement(d.key, "keep", None, (), (), "dropped: " + "; ".join(record.problems)), "fallback")

    def validate(self, state: Replacements, records: list[OutboxRecord]) -> list[str]:
        dossiers = [d for u in self.units for d in u.dossiers]
        problems = list(self.problems) + validate_replacements(state.replacements, state.sources, dossiers,
                                                                self.no_options, state.stale)
        return problems + consistent_units(state.replacements, self.units) + replay_problems(self, state, records)

    def write(self, state: Replacements, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.REPLACEMENTS, state.to_json())
