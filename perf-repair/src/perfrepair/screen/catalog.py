"""The screening catalog a step judges by: `screening.catalog` from perfrepair.yaml, else the packaged one (logged)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..catalog.names import Names
from ..catalog.screening import SCREENING, Screening
from ..config.load import Loaded
from ..inputs.resolve import Candidate
from ..inputs.table import SCREENING_CATALOG
from .handler import ScreeningHandler

PACKAGED = "packaged"


@dataclass(frozen=True)
class Catalog:
    path: Path
    sha256: str
    screening: Screening
    names: Names

    @property
    def source(self) -> str:
        return PACKAGED if self.path == SCREENING else str(self.path)

    def identity(self) -> dict:
        return {"source": self.source, "sha256": self.sha256}

    def handler(self) -> ScreeningHandler:
        return ScreeningHandler(self.screening, self.names)


def load_catalog(path: Path, names: Names | None = None) -> Catalog:
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    # catalog names without a probe's aliases: the run-level verdicts recorded canonical names already
    names = names or Names.load()
    return Catalog(path, digest, Screening.load(path, names=names), names)


def ai_review(loaded: Loaded | None) -> bool:
    return bool(loaded and loaded.value("screening.aiReview", default=False))


def screening_catalog(loaded: Loaded | None) -> Catalog:
    """None stands for no perfrepair.yaml; a set catalog that does not load is missing_file, never the packaged one."""
    where = f"screening.catalog unset in {loaded.file}" if loaded and loaded.file else "no perfrepair.yaml"
    set_value = loaded.value("screening.catalog") if loaded else None
    explicit = [Candidate(set_value, f"file {loaded.file} screening.catalog" if loaded else "settings")]
    note = f"({where}); aiReview {'on' if ai_review(loaded) else 'off'}"
    return SCREENING_CATALOG.resolve(explicit, load_catalog, note).value
