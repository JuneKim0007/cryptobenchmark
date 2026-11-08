"""Select over an app's units: the items from dossiers.json, the replacement rows code writes for a pick, replacements.json."""
from __future__ import annotations

from pathlib import Path

from ... import run_dir as rd
from ...data_handler.inbound.manifest import display_units
from ...data_handler.inbound.primitives import read_primitives
from ...dto.change import DROP_IN
from ...dto.decision import OutboxRecord
from ...dto.perf_mode import GENERIC_MODE, PerfMode
from ...dto.primitives import PrimitivesTable
from ...dto.replacement import Replacement, read_replacements
from ...dto.unit import UnitDossiers
from ...files import json_text, sha256_text
from ...result.gain import IMPROVED, WORSE, by_change
from ...result.upgrades import edits_of
from ...validation import require
from ...validation.dossiers.document import perf_of
from ...validation.dossiers.parse import parse_dossiers
from ...validation.replacements import consistent_units, validate_replacements
from .candidate import RECOMMEND, REPLACE, Candidate, SelectItem
from .render import render
from .replacements import Replacements
from .rows import digest_input
from .unit_candidates import unit_candidates

LLM, FALLBACK, STATIC = "llm", "fallback", "static"


def evidence(u: UnitDossiers, perf: PerfMode, table: PrimitivesTable | None = None, warnings: tuple[str, ...] = ()) -> str:
    """What the unit is decided on: its entry, dossiers, perfMode, the primitives.tsv numbers and the run warnings shown;
    another digest asks it again."""
    shown = {"lines": [digest_input(d, table) for d in u.dossiers]} if table is not None else {}
    shown |= {"warnings": list(warnings)} if warnings else {}
    return sha256_text(json_text({"unit": u.entry(), "dossiers": [d.to_json() for d in u.dossiers], "perfMode": perf.to_json(),
                                  **shown}))


def label(u: UnitDossiers) -> str:
    first = u.dossiers[0].scope
    return f"{first.file}:{first.line}" + (f" +{len(u.dossiers) - 1}" if len(u.dossiers) > 1 else "")


class UnitSource:
    """One app's units; a unit with no applicable candidate is still asked, with none as its only answer."""

    def __init__(self, run_path: Path, app: str):
        paths = rd.AppPaths(run_path, app)
        self.app, self.paths, self.folder = app, paths, paths.replace
        self.doc = rd.read_dossiers(paths.dossiers)
        self.table = read_primitives(run_path) if (Path(run_path) / rd.PRIMITIVES).is_file() else None
        self.display = display_units(run_path)
        # a folder before measurements.json has no run warnings to show
        self.warnings = tuple(rd.load_measurements(run_path).comparability) if (Path(run_path) / rd.MEASUREMENTS).is_file() else ()
        self.units, self.no_options, self.problems = parse_dossiers(self.doc, app)
        self.perf = perf_of(self.doc) or GENERIC_MODE
        self.max_change = self.doc.get("maxChange", DROP_IN)
        self.state = Replacements(app)
        for scope, reason in self.no_options.items():
            self.state.put(Replacement(scope, "keep", None, (), (), reason), STATIC)

    def items(self) -> list[SelectItem]:
        # a dossiers.json that does not hold together stops before the first question
        require(f"{self.app} dossiers", self.problems)
        out = []
        for u in self.units:
            found = unit_candidates(u, self.perf, self.max_change)
            text = render(u, self.perf, self.table, self.display, self.warnings, self.doc.get("measured"), found)
            out.append(SelectItem(u.key, label(u), tuple(found), True, evidence(u, self.perf, self.table, self.warnings), text, u))
        return out

    def decide(self, item: SelectItem, chosen: Candidate | None, reason: str) -> dict:
        u: UnitDossiers = item.source
        if chosen is None:
            return {"replacements": [Replacement(d.key, "keep", None, (), (), reason).to_json() for d in u.dossiers]}
        rows = []
        for p in chosen.picks:
            o, worse = p.option, by_change(p.option.estimates, WORSE)
            edits = edits_of(p.dossier.current, o) if chosen.decision == REPLACE else ()
            rows.append(Replacement(p.dossier.key, chosen.decision, o.item, edits, p.risks, reason,
                                    tuple(by_change(o.estimates, IMPROVED)), tuple(worse) if self.perf.overall else (),
                                    chosen.needs if chosen.decision == RECOMMEND else ()).to_json())
        return {"replacements": rows}

    def edits_code(self, item: SelectItem, chosen: Candidate) -> bool:
        return chosen.decision == REPLACE and any(edits_of(p.dossier.current, p.option) for p in chosen.picks)

    def unidentified(self, item: SelectItem, reason: str) -> dict:
        return {"unidentified": reason}

    def apply(self, item: SelectItem, record: OutboxRecord) -> None:
        u: UnitDossiers = item.source
        if record.outcome == "decided" and "replacements" in record.decision:
            for row in record.decision["replacements"]:
                self.state.put(Replacement.from_json(row), LLM)
            return
        why = f"review: {record.decision['unidentified']}" if record.decision else "dropped: " + "; ".join(record.problems)
        for d in u.dossiers:
            self.state.put(Replacement(d.key, "keep", None, (), (), why), FALLBACK)

    def documents(self) -> dict:
        return {self.paths.replacements: self.state.to_json()}

    def state_problems(self) -> list[str]:
        return self._problems(self.state.replacements, self.state.sources)

    def document_problems(self, doc: dict) -> list[str]:
        return self._problems(read_replacements(doc), doc["sources"])

    def _problems(self, replacements: dict, sources: dict) -> list[str]:
        dossiers = [d for u in self.units for d in u.dossiers]
        return (list(self.problems) + validate_replacements(replacements, sources, dossiers, self.no_options)
                + consistent_units(replacements, self.units))
