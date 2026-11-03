"""rows + measurements + run-level screen statuses → the primitives table: one line per primitive, input sizes as columns."""
from __future__ import annotations

from collections import defaultdict

from ..dto import PrimitiveRow, Summary
from ..dto.grouping import Item, qualified
from ..dto.metrics import METRICS
from ..dto.primitives import PrimitiveLine, PrimitivesTable, column, rounded
from ..dto.screen import Verdict
from ..stop.halt import Coded

WORK_FIELDS = ("type", "algorithm", "provider", "operation", "keySize", "phase")
Cells = dict[int | None, dict[str, Summary]]


def statuses(items: list[Item], screen: dict[int, Verdict]) -> dict[str, str]:
    """screen.json's run-level status by qualified name; no groups.json needed, so the device stage can build it."""
    return {i.qualified: screen[i.id].status for i in items if i.id in screen}


def _order(values: tuple) -> tuple:
    return tuple((v is None, "" if v is None else v) for v in values)


def _line(key: tuple, cells: Cells, sizes: dict[str, list[int | None]]) -> PrimitiveLine:
    medians = {column(m, size): rounded(cells[size][m].median) if m in cells.get(size, {}) else None
               for m, found in sizes.items() for size in found}
    # the noisiest input size speaks for the line
    cv = {m: rounded(max((by[m].cv for by in cells.values() if m in by and by[m].cv is not None), default=None))
          for m in sizes}
    # per metric its fewest runs at any input size
    n = {m: min((by[m].n for by in cells.values() if m in by), default=None) for m in sizes}
    return PrimitiveLine(*key, medians, n, cv)


def _grouped(rows: list[PrimitiveRow], measurements: dict[str, dict[str, Summary]],
             status_of: dict[str, str]) -> dict[tuple, Cells]:
    grouped: dict[tuple, Cells] = defaultdict(dict)
    for r in rows:
        name = qualified(r.type, r.algorithm, r.provider)
        if name not in status_of:
            raise Coded(f"primitive_not_screened: {name} has no screen.json verdict; rerun grouping build")
        key = (*(getattr(r, f) for f in WORK_FIELDS), status_of[name])
        if r.inputSize in grouped[key]:
            raise Coded(f"primitive_line_collision: {r.rowId} repeats {key} at input size {r.inputSize}")
        grouped[key][r.inputSize] = measurements.get(r.rowId) or {}
    return grouped


def _sizes(grouped: dict[tuple, Cells]) -> dict[str, list[int | None]]:
    """Per metric with runs, the input sizes it was measured at, the size-less column last."""
    found = {m.name: {size for cells in grouped.values() for size, by in cells.items() if m.name in by} for m in METRICS}
    return {m: sorted(s, key=lambda size: _order((size,))) for m, s in found.items() if s}


def build_table(rows: list[PrimitiveRow], measurements: dict[str, dict[str, Summary]],
                status_of: dict[str, str]) -> PrimitivesTable:
    """Every measured row, deprecated ones included with their status: a site's current call needs its own line."""
    grouped = _grouped(rows, measurements, status_of)
    sizes = _sizes(grouped)
    columns = tuple(column(m, size) for m, ordered in sizes.items() for size in ordered)
    return PrimitivesTable(columns, tuple(sizes), tuple(_line(k, grouped[k], sizes) for k in sorted(grouped, key=_order)))
