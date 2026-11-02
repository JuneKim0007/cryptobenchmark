"""Each input's policy as one row: its name, Need, the setting that names it and the packaged default."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from ..catalog.screening import SCREENING
from .resolve import Candidate, Need, Resolved, resolve


@dataclass(frozen=True)
class Policy:
    name: str
    need: Need
    setting: str | None = None
    packaged: Path | None = None
    label: str = "packaged default"

    def resolve(self, explicit: Iterable[Candidate], load: Callable[[Any], Any], note: str = "") -> Resolved:
        default = [Candidate(self.packaged, self.label, explicit=False, note=note)] if self.packaged else []
        return resolve(self.name, [*explicit, *default], load, self.need)


SCREENING_CATALOG = Policy("screening.catalog", Need.DEFAULT, "screening.catalog", SCREENING, "packaged catalog")
