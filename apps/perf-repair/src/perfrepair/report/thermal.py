"""A before/after pair's temperatures, from the per-case `thermal` block of the scoped benchmark.json: the block and
sleep as stored, and the labels code gives them; they change no verdict."""
from __future__ import annotations

from ..dto.report import THERMAL_MISMATCH, THERMAL_THROTTLED
from ..result.modes import criteria

SLEEP = "thermalThrottleSleepSeconds"


def _side(case: dict) -> dict:
    return {"thermal": case.get("thermal"), SLEEP: case.get(SLEEP)}


def start_gap(before: dict | None, after: dict | None) -> float | None:
    """The widest gap in degrees between the two start readings, over the sensors both name; None when one is absent."""
    a, b = (before or {}).get("start") or {}, (after or {}).get("start") or {}
    shared = a.keys() & b.keys()
    return round(max(abs(a[s] - b[s]) for s in shared), 3) if shared else None


def _throttled(block: dict | None) -> bool:
    return ((block or {}).get("endStatus") or 0) > 0


def labels(before: dict | None, after: dict | None) -> list[str]:
    gap = start_gap(before, after)
    return [*([THERMAL_MISMATCH] if gap is not None and gap > float(criteria()["thermalMismatchDegrees"]) else []),
            *([THERMAL_THROTTLED] if _throttled(before) or _throttled(after) else [])]


def thermal_row(before_case: dict | None, after_case: dict | None) -> dict | None:
    """None when neither side was measured or neither carries a block (a host run, a run before temperatures)."""
    if before_case is None or after_case is None or not (before_case.get("thermal") or after_case.get("thermal")):
        return None
    before, after = before_case.get("thermal"), after_case.get("thermal")
    return {"before": _side(before_case), "after": _side(after_case), "startGap": start_gap(before, after),
            "labels": labels(before, after)}
