"""The primitives.tsv lines a member is shown: its current item's and each option's, at the scope's key size and
operations, in the selected metrics' columns, time in the display units."""
from __future__ import annotations

from dataclasses import asdict

from ....dto.grouping import parse_qualified
from ....dto.metrics import BY_NAME
from ....dto.perf_mode import PerfMode
from ....dto.primitives import ABSENT, PrimitiveLine, PrimitivesTable
from ....dto.report import THROUGHPUT, has_views
from ....dto.site import Dossier
from ....dto.units import DisplayUnits, number
from ....result.configurations import operations


def _size(column: str) -> int | None:
    size = column.split("@", 1)[1]
    return None if size == ABSENT else int(size)


def lines_of(d: Dossier, table: PrimitivesTable) -> list[tuple[str, PrimitiveLine]]:
    """(side, line): `current` or an option alias; the scope's key size, lifecycle operations when known, and its
    pattern's variant only."""
    ops, key, variant = operations(d.scope), d.scope.keySize, d.scope.pattern
    sides = [("current", d.current)] + [(o.alias, o.item) for o in d.options]
    out = []
    for side, item in sides:
        engine, name, provider = parse_qualified(item)
        out += [(side, line) for line in table.lines if (line.type, line.algorithm, line.provider) == (engine, name, provider)
                and (not ops or line.operation in ops) and key in (None, line.keySize) and line.variant == variant]
    return out


def digest_input(d: Dossier, table: PrimitivesTable | None) -> list[dict]:
    """The stored numbers behind the shown lines, never the display text: a unit change marks nothing stale."""
    return [] if table is None else [{"side": side, **asdict(line)} for side, line in lines_of(d, table)]


def _columns(table: PrimitivesTable, perf: PerfMode, units: DisplayUnits) -> list[tuple[str, str, object]]:
    """(header, stored column, converter) per shown column: latency and throughput views of time, one metric."""
    out = []
    for c in table.columns:
        metric = BY_NAME.get(c.split("@", 1)[0])
        if metric is None or metric.name not in perf.names:
            continue
        if not has_views(metric):
            out.append((c, c, lambda x: x))
            continue
        size, at = _size(c), c.split("@", 1)[1]
        views = perf.views(metric)
        rate = THROUGHPUT in views and units.throughput_of(1.0, size) is not None
        # throughput alone still shows time where its unit has no input size to divide
        if not rate or len(views) > 1:
            out.append((f"latency@{at}", c, units.latency_of))
        if rate:
            out.append((f"throughput@{at}", c, lambda ns, s=size: units.throughput_of(ns, s)))
    return out


def render_lines(d: Dossier, table: PrimitivesTable, perf: PerfMode, units: DisplayUnits) -> list[str]:
    found = lines_of(d, table)
    if not found:
        return ["MEASURED", "  no primitives.tsv line at this site's key size and operations"]
    # a column no shown line has a value in says nothing
    columns = [x for x in _columns(table, perf, units) if any(line.medians.get(x[1]) is not None for _, line in found)]
    metrics = [m for m in perf.names if m in table.metrics]
    return _head(columns, metrics, units) + ["  " + " | ".join(_cells(side, line, columns, metrics)) for side, line in found]


def _head(columns, metrics: list[str], units: DisplayUnits) -> list[str]:
    timed = any(has_views(BY_NAME[m]) for m in metrics)
    unit_note = f"latency {units.latency_label}, throughput {units.throughput}; " if timed else ""
    head = ["side", "operation", "key", "phase", "status", *(h for h, _, _ in columns), *(f"{m} n" for m in metrics),
            *(f"{m} cv" for m in metrics)]
    return [f"MEASURED (primitives.tsv medians per input size; {unit_note}other metrics in their registry units)",
            "  " + " | ".join(head)]


def _shown(x, text) -> str:
    return ABSENT if x is None else text(x)


def _cells(side: str, line: PrimitiveLine, columns, metrics: list[str]) -> list[str]:
    cells = [side, line.operation, _shown(line.keySize, str), line.phase or ABSENT, line.status]
    cells += [_shown(line.medians.get(c), lambda x, f=f: number(f(x))) for _, c, f in columns]
    return (cells + [_shown(line.n.get(m), str) for m in metrics]
            + [_shown(line.cv.get(m), lambda x: f"{x:.3f}") for m in metrics])
