"""primitives.tsv: its shape, registry metrics and screen statuses, and equal to what rows, measurements and screen.json make."""
from __future__ import annotations

from collections import Counter

from ..dto import Measurements, PrimitiveRow
from ..dto.metrics import NAMES
from ..dto.primitives import PrimitivesTable
from ..dto.screen import STATUSES
from ..result.primitives import build_table


def _columns(table: PrimitivesTable) -> list[str]:
    problems = [f"column {c}: {c.split('@')[0]} is not a registry metric" for c in table.columns if c.split("@")[0] not in NAMES]
    return problems + [f"cv column {m}: not a registry metric" for m in table.metrics if m not in NAMES]


def _shape(table: PrimitivesTable) -> list[str]:
    problems = [f"line {k}: repeated" for k, n in Counter(line.key for line in table.lines).items() if n > 1]
    problems += _columns(table)
    problems += [f"line {line.key}: status {line.status!r} is not in {list(STATUSES)}" for line in table.lines
                 if line.status not in STATUSES]
    return problems + [f"line {line.key}: {m} n {n} is below 1" for line in table.lines for m, n in line.n.items()
                       if n is not None and n < 1]


def validate_primitives(table: PrimitivesTable, rows: list[PrimitiveRow], measurements: Measurements,
                        status_of: dict[str, str]) -> list[str]:
    problems = _shape(table)
    try:
        expected = build_table(rows, measurements.byRow, status_of)
    except ValueError as e:
        return problems + [str(e)]
    if table.header != expected.header:
        return problems + [f"header {list(table.header)} is not {list(expected.header)}"]
    made = {line.key: line for line in expected.lines}
    problems += [f"line {line.key}: not the line rows, measurements and screen.json make" for line in table.lines
                 if made.get(line.key) != line]
    kept = {line.key for line in table.lines}
    return problems + [f"line {k}: missing" for k in made if k not in kept]
