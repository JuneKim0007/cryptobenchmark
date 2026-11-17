"""The session's end: one summary row per target and suite (state, code, results), written to the session folder and printed."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from cryptobench.shared.document.write import write_text

COLUMNS = ("target", "suite", "state", "code", "results")


@dataclasses.dataclass(frozen=True)
class Row:
    target: str
    suite: str
    state: str
    code: str | None = None
    results: str | None = None


def table(rows: list[Row]) -> list[str]:
    cells = [COLUMNS] + [(r.target, r.suite, r.state, r.code or "-", r.results or "-") for r in rows]
    widths = [max(len(c[i]) for c in cells) for i in range(len(COLUMNS))]
    return ["  ".join(cell.ljust(width) for cell, width in zip(c, widths)).rstrip() for c in cells]


def written(rows: list[Row], path: Path) -> Path:
    return write_text(path, "\n".join(table(rows)) + "\n")
