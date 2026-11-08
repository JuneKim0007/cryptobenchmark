"""Select over an app's broken uses: the upgrade list's and the unreachable ones settled by code, the rest asked with the
ranked secure options as candidates and no none; upgrades.json."""
from __future__ import annotations

from pathlib import Path

from ... import run_dir as rd
from ...dto.decision import OutboxRecord
from ...dto.dossier import NO_SECURE_OPTION, PERSON_JUDGES, reason_code
from ...dto.perf_mode import GENERIC_MODE
from ...dto.upgrade import (FALLBACK_SOURCE, LIST_SOURCE, MODEL_SOURCE, NEEDS_MIGRATION, NO_SECURE, NOT_REACHED, STATIC_SOURCE,
                            Upgrade, UpgradeItem, read_upgrades)
from ...files import json_text, sha256_text
from ...result.upgrades import edits_of, needs_person, settled
from ...validation.dossiers.document import perf_of
from ...validation.upgrade import validate_upgrades
from .candidate import UPGRADE, Candidate, SelectItem
from .upgrade_render import render
from .upgrade_state import UpgradeState

LISTED_REASON = "the upgrade list's target with the best measured performance"
MODEL_DROPPED, REVIEW_UNIDENTIFIED = "model_dropped", "review_unidentified"


def _unreached(n: dict) -> Upgrade:
    """A broken use with no option: a person's when accepted, measured members were refused, else its reason's status."""
    if reason_code(n["reason"]) == PERSON_JUDGES:
        needs = tuple(n["reason"].split(": ", 1)[1].split(", "))
        return Upgrade(n["scope"], n["current"], NEEDS_MIGRATION, None, STATIC_SOURCE, n["reason"], needs=needs)
    status = NO_SECURE if n["reason"] == NO_SECURE_OPTION else NOT_REACHED
    return Upgrade(n["scope"], n["current"], status, None, STATIC_SOURCE, n["reason"])


class UpgradeSource:

    def __init__(self, run_path: Path, app: str):
        paths = rd.AppPaths(run_path, app)
        self.app, self.paths, self.folder = app, paths, paths.upgrade
        self.doc = rd.read_dossiers(paths.dossiers)
        self.perf = perf_of(self.doc) or GENERIC_MODE
        self.rows = [UpgradeItem.from_json(r) for r in self.doc["upgrades"]]
        self.state = UpgradeState(app)
        for u in self.rows:
            if u.identified:
                self.state.rows[u.key] = settled(u, u.dossier.options[0], LIST_SOURCE, LISTED_REASON)
        for n in self.doc["brokenUnreached"]:
            self.state.rows[n["scope"]] = _unreached(n)

    def items(self) -> list[SelectItem]:
        out = []
        for u in (u for u in self.rows if not u.identified):
            s = u.dossier.scope
            found = tuple(Candidate(o.alias, o.item, UPGRADE, option=o) for o in u.dossier.options)
            digest = sha256_text(json_text({"perfMode": self.perf.to_json(), "item": u.to_json()}))
            out.append(SelectItem(u.key, f"{s.file}:{s.line}", found, False, digest, render(u), u))
        return out

    def decide(self, item: SelectItem, chosen: Candidate | None, reason: str) -> dict:
        return {"option": chosen.item, "reason": reason}

    def edits_code(self, item: SelectItem, chosen: Candidate) -> bool:
        return not needs_person(item.source, chosen.option) and bool(edits_of(item.source.dossier.current, chosen.option))

    def unidentified(self, item: SelectItem, reason: str) -> dict:
        return {"unidentified": reason}

    def apply(self, item: SelectItem, record: OutboxRecord) -> None:
        u: UpgradeItem = item.source
        if record.outcome == "decided" and "option" in record.decision:
            option = next(o for o in u.dossier.options if o.item == record.decision["option"])
            self.state.rows[u.key] = settled(u, option, MODEL_SOURCE, record.decision["reason"])
            return
        why, need = ((f"review: {record.decision['unidentified']}", REVIEW_UNIDENTIFIED) if record.decision
                     else ("dropped: " + "; ".join(record.problems), MODEL_DROPPED))
        self.state.rows[u.key] = Upgrade(u.key, u.dossier.current, NEEDS_MIGRATION, None, FALLBACK_SOURCE, why, needs=(need,))

    def documents(self) -> dict:
        return {self.paths.upgrades: self.state.to_json()}

    def state_problems(self) -> list[str]:
        return validate_upgrades(list(self.state.rows.values()), {u.key: u for u in self.rows})

    def document_problems(self, doc: dict) -> list[str]:
        return validate_upgrades(read_upgrades(doc), {u.key: u for u in self.rows})
