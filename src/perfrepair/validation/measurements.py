"""measurements.json: keyed by known rows; every summary ordered (p25 ≤ median ≤ p75), positive, n ≥ 1."""
from __future__ import annotations

import math

from ..dto import Measurements, PrimitiveRow, Summary


def _summary(where: str, s: Summary) -> list[str]:
    values = (s.median, s.p25, s.p75)
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values):
        return [f"{where}: a value is not a finite number"]
    problems = []
    if not s.p25 <= s.median <= s.p75:
        problems.append(f"{where}: p25 {s.p25} ≤ median {s.median} ≤ p75 {s.p75} does not hold")
    if s.n < 1:
        problems.append(f"{where}: n is {s.n}")
    if s.cv is not None and s.cv < 0:
        problems.append(f"{where}: cv {s.cv} is negative")
    return problems


def validate_measurements(m: Measurements, rows: list[PrimitiveRow]) -> list[str]:
    known = {r.rowId for r in rows}
    problems = [f"{rid}: no such row" for rid in sorted(set(m.byRow) - known)]
    for rid, metrics in sorted(m.byRow.items()):
        t = metrics.get("timeNs")
        if t is None:
            problems.append(f"{rid}: timeNs missing")
            continue
        problems += _summary(f"{rid}.timeNs", t)
        if t.median <= 0:
            problems.append(f"{rid}.timeNs: median {t.median} is not positive")
        if (a := metrics.get("allocations")) is not None:
            problems += _summary(f"{rid}.allocations", a)
    return problems
