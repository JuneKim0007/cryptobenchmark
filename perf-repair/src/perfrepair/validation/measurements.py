from __future__ import annotations

import math

from ..dto import Measurements, PrimitiveRow, Summary
from ..dto.metrics import BY_NAME, METRICS, Metric


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


def _metric(where: str, metric: Metric, s: Summary) -> list[str]:
    problems = _summary(where, s)
    if metric.positive and isinstance(s.median, (int, float)) and s.median <= 0:
        problems.append(f"{where}: median {s.median} is not positive")
    if metric.kinds and s.kind not in metric.kinds:
        problems.append(f"{where}: kind {s.kind!r} is not {' or '.join(metric.kinds)}")
    if not metric.kinds and s.kind is not None:
        problems.append(f"{where}: kind {s.kind!r} on a metric without kinds")
    return problems


def validate_measurements(m: Measurements, rows: list[PrimitiveRow]) -> list[str]:
    known = {r.rowId for r in rows}
    problems = [f"{rid}: no such row" for rid in sorted(set(m.byRow) - known)]
    for rid, summaries in sorted(m.byRow.items()):
        problems += [f"{rid}.{name}: not a registry metric" for name in sorted(set(summaries) - set(BY_NAME))]
        for metric in METRICS:
            s = summaries.get(metric.name)
            if s is None:
                problems += [f"{rid}: {metric.name} missing"] if metric.required else []
                continue
            problems += _metric(f"{rid}.{metric.name}", metric, s)
    return problems
