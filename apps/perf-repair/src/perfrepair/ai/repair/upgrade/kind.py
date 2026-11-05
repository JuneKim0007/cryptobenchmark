from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .... import run_dir as rd
from ....dto.change import MIGRATION
from ....dto.decision import OutboxRecord
from ....dto.dossier import NO_SECURE_OPTION
from ....dto.perf_mode import GENERIC_MODE
from ....dto.prompt import Charter, TaskPrompt
from ....dto.upgrade import FALLBACK_SOURCE, LIST_SOURCE, MODEL_SOURCE, NEEDS_MIGRATION, NO_SECURE, NOT_REACHED, STATIC_SOURCE, Upgrade, UpgradeItem
from ....files import json_text, sha256_text, write_json
from ....result.upgrades import settled
from ....validation.dossiers.document import perf_of
from ....validation.dossiers.dossier import check_dossier
from ....validation.upgrade import check_reply, validate_upgrades
from ...runtime.engine.kind import replay_problems
from ...runtime.prompt import PromptLibrary
from .render import render
from .schema import SCHEMA
from .state import UpgradeState

NAME = "repair/upgrade"
LISTED_REASON = "the upgrade list's target with the best measured performance"
MODEL_DROPPED = "model_dropped"


def charter(library: PromptLibrary, inputs: str = "") -> Charter:
    return library.charter(NAME, SCHEMA, inputs)


@dataclass(frozen=True)
class Asked:
    """An unlisted broken use: the engine's item."""
    item: UpgradeItem

    @property
    def key(self) -> str:
        return self.item.key


class UpgradeKind:
    name = "repair-upgrade"

    def __init__(self, app: str, doc: dict, directory: Path):
        self.app, self.doc, self.directory = app, doc, Path(directory)
        self.perf = perf_of(doc) or GENERIC_MODE
        self.rows = [UpgradeItem.from_json(r) for r in doc["upgrades"]]
        self.by_key = {u.key: u for u in self.rows}

    def inputs(self) -> str:
        """The asked items' digest: a changed candidate list opens a new outbox, so an answer never outlives what it saw."""
        return sha256_text(json_text({"perfMode": self.perf.to_json(), "items": [a.item.to_json() for a in self.items()]}))

    def items(self) -> list[Asked]:
        return [Asked(u) for u in self.rows if not u.identified]

    def pending(self) -> list[Asked]:
        return self.items()

    def empty(self) -> UpgradeState:
        """What no model is needed for: the list's first measured target, and each broken use with nothing to offer."""
        state = UpgradeState(self.app)
        for u in self.rows:
            if u.identified:
                state.rows[u.key] = settled(u, u.dossier.options[0], LIST_SOURCE, LISTED_REASON)
        for n in self.doc["brokenUnreached"]:
            status = NO_SECURE if n["reason"] == NO_SECURE_OPTION else NOT_REACHED
            state.rows[n["scope"]] = Upgrade(n["scope"], n["current"], status, None, STATIC_SOURCE, n["reason"])
        return state

    def admit(self, a: Asked) -> list[str]:
        return check_dossier(a.item.to_json(), self.app, self.perf, MIGRATION, gained=False)[1]

    def label(self, a: Asked) -> str:
        s = a.item.dossier.scope
        return f"{s.file}:{s.line}"

    def render(self, a: Asked, state: UpgradeState) -> TaskPrompt:
        return TaskPrompt(NAME, render(a.item), a.key)

    def check(self, a: Asked, text: str, state: UpgradeState) -> tuple[dict | None, list[str]]:
        return check_reply(text, a.item)

    def apply(self, state: UpgradeState, a: Asked, record: OutboxRecord) -> None:
        state.version += 1
        if record.outcome == "decided":
            option = next(o for o in a.item.dossier.options if o.item == record.decision["option"])
            state.rows[a.key] = settled(a.item, option, MODEL_SOURCE, record.decision["reason"])
            return
        state.rows[a.key] = Upgrade(a.key, a.item.dossier.current, NEEDS_MIGRATION, None, FALLBACK_SOURCE,
                                    "dropped: " + "; ".join(record.problems), needs=(MODEL_DROPPED,))

    def validate(self, state: UpgradeState, records: list[OutboxRecord]) -> list[str]:
        return validate_upgrades(list(state.rows.values()), self.by_key) + replay_problems(self, state, records)

    def write(self, state: UpgradeState, records: list[OutboxRecord]) -> None:
        write_json(self.directory / rd.UPGRADES, state.to_json())
