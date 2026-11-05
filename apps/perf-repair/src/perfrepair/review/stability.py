"""Whether the replacement decision is stable: N sampled units, each asked K times on the message `ai replace` sends, picks
compared free text left out → review/stability.json; each ask an engine item in review/stability, no replace decision changes."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path

from .. import run_dir as rd
from ..ai.runtime.agent import Conversations
from ..ai.runtime.engine.ask import Limits
from ..ai.runtime.engine.decide import decide
from ..ai.runtime.engine.events import Where
from ..ai.runtime.engine.kind import replay_problems
from ..ai.runtime.engine.tracking import role_run
from ..ai.runtime.prompt import PromptLibrary
from ..ai.suggest.site_replace.command import site_kind
from ..ai.suggest.site_replace.kind import SiteReplaceKind, charter
from ..dto.decision import OutboxRecord
from ..dto.prompt import TaskPrompt
from ..dto.unit import UnitDossiers
from ..files import sha256_text
from .sheet import choice

# a fixed draw, so two runs sample the same units
SEED = 1


@dataclass(frozen=True)
class Ask:
    key: str
    kind: SiteReplaceKind
    unit: UnitDossiers


@dataclass
class Picks:
    version: int = 0
    units: dict[str, list[str | None]] = field(default_factory=dict)

    def to_json(self) -> dict:
        return {"version": self.version, "units": self.units}


class StabilityKind:
    name = "review-stability"

    def __init__(self, device: Path, sample: int, asks: int):
        self.device, self.asks = Path(device), asks
        units = [(kind, u) for kind in self._apps() for u in kind.items()]
        self.chosen = random.Random(SEED).sample(units, min(sample, len(units)))
        self._items = [Ask(f"{kind.app}/{u.key}#{n}", kind, u) for kind, u in self.chosen for n in range(1, asks + 1)]

    def _apps(self) -> list[SiteReplaceKind]:
        return [site_kind(self.device, f.name) for f in rd.app_dirs(self.device) if (f / rd.DOSSIERS).is_file()]

    @property
    def inputs(self) -> str:
        """The messages: another draw or changed dossiers start a new outbox, the same ones make no call."""
        return "asked " + sha256_text("\0".join(f"{a.key}\0{self.render(a, None).text}" for a in self._items))

    def items(self) -> list[Ask]:
        return self._items

    def pending(self) -> list[Ask]:
        return self._items

    def empty(self) -> Picks:
        return Picks()

    def admit(self, a: Ask) -> list[str]:
        return a.kind.admit(a.unit)

    def label(self, a: Ask) -> str:
        return a.key

    def render(self, a: Ask, state: Picks | None) -> TaskPrompt:
        message = a.kind.render(a.unit, None)
        return TaskPrompt(message.name, message.text, a.key)

    def check(self, a: Ask, text: str, state: Picks) -> tuple[dict | None, list[str]]:
        return a.kind.check(a.unit, text, None)

    def apply(self, state: Picks, a: Ask, record: OutboxRecord) -> None:
        pick = choice(record.decision) if record.outcome == "decided" else None
        state.units.setdefault(f"{a.kind.app}/{a.unit.key}", []).append(pick)
        state.version += 1

    def validate(self, state: Picks, records: list[OutboxRecord]) -> list[str]:
        return replay_problems(self, state, records)

    def document(self, state: Picks) -> dict:
        rows = []
        for kind, u in self.chosen:
            picks = state.units.get(f"{kind.app}/{u.key}", [])
            rows.append({"app": kind.app, "unit": u.key, "picks": picks, "stable": None not in picks and len(set(picks)) == 1})
        return {"sample": len(rows), "asks": self.asks, "stable": sum(r["stable"] for r in rows), "units": rows}

    def documents(self, state: Picks, records: list[OutboxRecord]) -> dict:
        return {rd.review_stability(self.device): self.document(state)}


def stability(device: Path, conversations: Conversations, library: PromptLibrary, sample: int, asks: int,
              limits: Limits = Limits()) -> dict:
    with role_run("review.stability", device):
        kind = StabilityKind(device, sample, asks)
        rd.review_stability(device).parent.mkdir(parents=True, exist_ok=True)
        state = decide(kind, charter(library, kind.inputs), conversations, rd.review_stability_folder(device), limits,
                       echo=lambda _: None, where=Where("review", "stability"))
        return kind.document(state)
