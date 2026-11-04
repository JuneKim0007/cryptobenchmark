"""The cases a delta will plan and the time they take, from the stored run's own plan and its transcripts' took: lines."""
from __future__ import annotations

import re
import statistics
from pathlib import Path

from .. import run_dir as rd
from ..dto.benchmark_coverage import Gap
from ..dto.grouping import parse_qualified

TOOK = re.compile(r"^took:\s+prepare and measure in (?P<s>[0-9.]+)s$")


def seconds_per_case(folder: Path, measured: int) -> float | None:
    """The last benchmark's measuring time over its measured cases; None without a took: line."""
    logs = sorted((Path(folder) / rd.PIPELINE_LOGS).glob("*.log")) if (Path(folder) / rd.PIPELINE_LOGS).is_dir() else []
    took = [float(m["s"]) for p in logs for line in p.read_text(errors="replace").splitlines() if (m := TOOK.match(line))]
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
