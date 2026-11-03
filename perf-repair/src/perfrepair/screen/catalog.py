"""The screening catalog a step judges by: `device.screening.catalog` from perfrepair.yaml, else the packaged one (logged)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..catalog.names import Names
from ..stop.halt import Coded
from ..catalog.screening import SCREENING, Screening
from ..config.load import Loaded
from ..inputs.resolve import Candidate
from ..inputs.table import SCREENING_AI_REVIEW, SCREENING_CATALOG
from .handler import ScreeningHandler

PACKAGED = "packaged"


class CatalogMismatch(Coded):
    pass


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

    def mismatch(self, recorded: dict | None) -> list[str]:
        """A run is judged by one catalog: the one screen.json recorded; none recorded means no screening ran."""
        if recorded is None or recorded.get("sha256") == self.sha256:
            return []
        return [f"screening_catalog_mismatch: screen.json was screened by {recorded.get('source')} "
                f"(sha256 {str(recorded.get('sha256'))[:12]}), this step resolved {self.source} (sha256 {self.sha256[:12]}); "
                f"rerun grouping build or set device.screening.catalog to the catalog screen.json names"]

    def require_same(self, recorded: dict | None) -> None:
        problems = self.mismatch(recorded)
        if problems:
            raise CatalogMismatch(problems[0])


def load_catalog(path: Path, names: Names | None = None) -> Catalog:
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    # catalog names without a probe's aliases: the run-level verdicts recorded canonical names already
    names = names or Names.load()
    return Catalog(path, digest, Screening.load(path, names=names), names)


def ai_review(loaded: Loaded | None) -> bool:
    return bool(loaded and loaded.read(SCREENING_AI_REVIEW))


def screening_catalog(loaded: Loaded | None) -> Catalog:
    """None stands for no perfrepair.yaml; a set catalog that does not load is missing_file, never the packaged one."""
    key = SCREENING_CATALOG.key
    where = f"{key} unset in {loaded.file}" if loaded and loaded.file else "no perfrepair.yaml"
    set_value = loaded.read(SCREENING_CATALOG) if loaded else None
    explicit = [Candidate(set_value, f"file {loaded.file} {key}" if loaded else "settings")]
    note = f"({where}); aiReview {'on' if ai_review(loaded) else 'off'}"
    return SCREENING_CATALOG.resolve(explicit, load_catalog, note).value
