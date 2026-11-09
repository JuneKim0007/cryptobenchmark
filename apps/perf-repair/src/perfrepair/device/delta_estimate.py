"""The cases a delta will plan and the time they take, from the stored run's own plan and its transcripts' took: lines."""
from __future__ import annotations

import re
import statistics
from pathlib import Path

from cryptobench.paths import RunTree
from ..dto.benchmark_coverage import Gap
from cryptobench.catalogue.grouping import parse_qualified

DELTA_RESULTS = "/delta/results"
TOOK = re.compile(r"^took:\s+prepare and measure in (?P<s>[0-9.]+)s$")


def _whole_run_took(lines: list[str]) -> list[float]:
    """The took: lines of calls into the results root; a delta's call times a few cases, so it would read far too fast."""
    took, delta = [], False
    for line in lines:
        if line.startswith("$ "):
            delta = DELTA_RESULTS in line
        elif (m := TOOK.match(line)) and not delta:
            took.append(float(m["s"]))
    return took


def seconds_per_case(folder: Path, measured: int) -> float | None:
    """The last whole benchmark's measuring time over its cases; None without a took: line."""
    logs = sorted((RunTree(folder).log.pipeline).glob("*.log")) if (RunTree(folder).log.pipeline).is_dir() else []
    took = [t for p in logs for t in _whole_run_took(p.read_text(errors="replace").splitlines())]
    return took[-1] / measured if took and measured else None


def planned_cases(gaps: tuple[Gap, ...], anchors: frozenset[str], planned: dict[str, int]) -> int:
    """A lost case is one; an item never planned plans as many as the median stored item of its engine type."""
    by_type: dict[str, list[int]] = {}
    for item, n in planned.items():
        by_type.setdefault(parse_qualified(item)[0], []).append(n)
    every = list(planned.values()) or [1]
    items = {g.item for g in gaps} | set(anchors)
    lost = {g.item for g in gaps if g.case}
    unplanned = items - lost - set(anchors)
    count = sum(planned.get(i, 0) for i in lost | set(anchors))
    return count + sum(round(statistics.median(by_type.get(parse_qualified(i)[0], every))) for i in unplanned)


def estimate_line(cases: int, items: int, anchors: int, per_case: float | None) -> str:
    time = f"about {cases * per_case / 60:.1f} min at {per_case:.1f} s a case" if per_case else "time unknown: no earlier took: line"
    return f"delta:     {cases} cases of {items} gap items and {anchors} anchors, {time}"
