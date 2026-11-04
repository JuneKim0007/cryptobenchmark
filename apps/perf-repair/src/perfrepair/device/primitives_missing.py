"""MissingList: the one writer of log/details/primitives_missing.yaml. A run's rows per source, the file rewritten whole
on every change so a killed run leaves what it knew; the rows stay in memory, no stage reads the file back."""
from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

import yaml

from .. import run_dir as rd
from ..dto.event import FINDING
from ..dto.primitives_missing import MissingRow, missing_document, pointer_line
from ..files import write_text_making_parents
from ..log import emit, run_id
from ..validation import require
from ..validation.primitives_missing import validate_missing


class MissingList:
    def __init__(self):
        self.device: Path | None = None
        self._sources: dict[str, list[MissingRow]] = {}
        self._pointed = False

    @property
    def path(self) -> Path | None:
        return self.device / rd.PRIMITIVES_MISSING if self.device else None

    def open(self, device: Path) -> None:
        """The folder is known: a clean run ends on an empty list, never on the last run's."""
        self.device = Path(device)
        self._write()

    def put(self, source: str, rows: Iterable[MissingRow]) -> None:
        """Replaces what this source said before, so a step run twice counts its sites once."""
        self._sources[source] = list(rows)
        self._write()
        self._point()

    def rows(self) -> list[MissingRow]:
        merged: dict[tuple, MissingRow] = {}
        for rows in self._sources.values():
            for r in rows:
                merged[r.key] = merged[r.key].merged(r) if r.key in merged else r
        return [merged[k] for k in sorted(merged)]

    def _write(self) -> None:
        if self.device is None:
            return
        doc = missing_document(run_id(), self.rows())
        require(rd.PRIMITIVES_MISSING, validate_missing(doc))
        write_text_making_parents(self.path, yaml.safe_dump(doc, sort_keys=False))

    def _point(self) -> None:
        # one event, so status.log says it once however many findings it sits among
        if self._pointed or self.device is None or not self.rows():
            return
        self._pointed = True
        emit("device", "primitives_missing", FINDING, detail=pointer_line(self.path), ref=rd.PRIMITIVES_MISSING,
             data={"pointer": True})

    def announce(self, echo: Callable[[str], None]) -> None:
        if self.device is not None and self.rows():
            echo(pointer_line(self.path))
