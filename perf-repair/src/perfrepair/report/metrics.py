"""One scope's before and after cases → a row per reported metric: medians, ratio, pImprove and its level."""
from __future__ import annotations

from ..data_handler.inbound.results import summarise
from ..dto.measurement import ESTIMATED, MEASURED
from ..dto.report import REPORTED
from ..dto.site import ENERGY_KINDS_DIFFER
from ..result.confidence import level
from ..result.estimate import p_improve

NS_PER_SECOND, BYTES_PER_MB = 1e9, 1e6


def unmeasured(reason: str) -> list[dict]:
    return [{"metric": m, "unit": u, "measured": False, "reason": reason} for m, u in REPORTED]


def _runs(case: dict, metric: str) -> list[float] | None:
    block = (case.get("metrics") or {}).get(metric)
    return block["runs"] if block and block.get("runs") else None


def _kind(case: dict, metric: str) -> str:
    return ((case.get("metrics") or {}).get(metric) or {}).get("kind", MEASURED)


def _throughput(before: float, after: float, input_size: int | None) -> dict:
    ops = {"before": NS_PER_SECOND / before, "after": NS_PER_SECOND / after}
    mb = None if input_size is None else {k: v * input_size / BYTES_PER_MB for k, v in ops.items()}
    return {"opsPerSecond": ops, "mbPerSecond": mb}


def _not_comparable(metric: str, before_case: dict, after_case: dict) -> str | None:
    missing = [side for side, case in (("before", before_case), ("after", after_case)) if _runs(case, metric) is None]
    if missing:
        return f"absent: no {metric} runs for {' and '.join(missing)} in benchmark.json"
    kinds = _kind(before_case, metric), _kind(after_case, metric)
    return f"{ENERGY_KINDS_DIFFER}: {kinds[0]} before, {kinds[1]} after" if kinds[0] != kinds[1] else None


def _row(metric: str, unit: str, before_case: dict, after_case: dict) -> dict:
    if reason := _not_comparable(metric, before_case, after_case):
        return {"metric": metric, "unit": unit, "measured": False, "reason": reason}
    before, after = summarise([_runs(before_case, metric)]), summarise([_runs(after_case, metric)])
    p = p_improve(before.processes, after.processes)
    # a zero median before (no allocations) has no ratio; pImprove still compares the runs
    ratio = after.median / before.median if before.median else None
    row = {"metric": metric, "unit": unit, "measured": True, "before": before.median, "after": after.median,
           "ratio": ratio, "pImprove": p, "level": level(p), "n": min(before.n, after.n)}
    if metric == "timeNs":
        positive = before.median > 0 and after.median > 0
        row["throughput"] = _throughput(before.median, after.median, before_case.get("inputSize")) if positive else None
    return row | ({"kind": ESTIMATED} if _kind(before_case, metric) == ESTIMATED else {})


def metric_rows(before_case: dict, after_case: dict) -> list[dict]:
    return [_row(metric, unit, before_case, after_case) for metric, unit in REPORTED]
