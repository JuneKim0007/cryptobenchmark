"""One scope's before and after cases → a row per reported metric: medians, ratio, pImprove and its level, and whether
the perfMode selected it; people see every metric, the model only the selected ones."""
from __future__ import annotations

from dataclasses import replace

from ..data_handler.inbound.results import summarise
from ..dto.measurement import ESTIMATED, MEASURED
from ..dto.metrics import BY_NAME
from ..dto.perf_mode import PerfMode
from ..dto.report import REPORTED, has_views
from ..dto.units import DisplayUnits
from ..result.confidence import level
from ..result.estimate import compare


def unmeasured(reason: str, perf: PerfMode) -> list[dict]:
    return [{"metric": m, "unit": u, "selected": m in perf.names, "measured": False, "reason": reason} for m, u in REPORTED]


def _runs(case: dict, metric: str) -> list[float] | None:
    block = (case.get("metrics") or {}).get(metric)
    return block["runs"] if block and block.get("runs") else None


def _kind(case: dict, metric: str) -> str:
    return ((case.get("metrics") or {}).get(metric) or {}).get("kind", MEASURED)


def views(before: float, after: float, input_size: int | None, units: DisplayUnits) -> dict:
    """The time metric in the display units; throughput null where its unit needs an input size the case has none of."""
    tput = [units.throughput_of(before, input_size), units.throughput_of(after, input_size)]
    return {"latency": {"unit": units.latency_label, "before": units.latency_of(before), "after": units.latency_of(after)},
            "throughput": None if None in tput else {"unit": units.throughput, "before": tput[0], "after": tput[1]}}


def _absent(metric: str, before_case: dict, after_case: dict) -> str | None:
    missing = [side for side, case in (("before", before_case), ("after", after_case)) if _runs(case, metric) is None]
    return f"absent: no {metric} runs for {' and '.join(missing)} in benchmark.json" if missing else None


def _side(case: dict, metric: str):
    return replace(summarise([_runs(case, metric)]), kind=_kind(case, metric))


def _row(metric: str, unit: str, selected: bool, before_case: dict, after_case: dict, units: DisplayUnits) -> dict:
    if reason := _absent(metric, before_case, after_case):
        return {"metric": metric, "unit": unit, "selected": selected, "measured": False, "reason": reason}
    before, after = _side(before_case, metric), _side(after_case, metric)
    c = compare(before, after, BY_NAME[metric].lowerIsBetter)
    if not c.comparable:
        return {"metric": metric, "unit": unit, "selected": selected, "measured": False, "reason": c.reason}
    row = {"metric": metric, "unit": unit, "selected": selected, "measured": True, "before": before.median, "after": after.median,
           "ratio": c.ratio, "pImprove": c.pImprove, "level": level(c.pImprove), "n": c.n}
    if has_views(BY_NAME[metric]):
        positive = before.median > 0 and after.median > 0
        row["views"] = views(before.median, after.median, before_case.get("inputSize"), units) if positive else None
    return row | ({"kind": ESTIMATED} if _kind(before_case, metric) == ESTIMATED else {})


def metric_rows(before_case: dict, after_case: dict, perf: PerfMode, units: DisplayUnits) -> list[dict]:
    return [_row(metric, unit, metric in perf.names, before_case, after_case, units) for metric, unit in REPORTED]
