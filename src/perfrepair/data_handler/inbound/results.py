"""benchmark.json + prepared.yaml → PrimitiveRows and their summarised measurements, computed once here."""
from __future__ import annotations

from ...files import read_yaml

import json
import math
import statistics
from pathlib import Path


from ...dto import PrimitiveRow, Summary

Measurements = dict[str, dict[str, Summary | None]]


def summarise(runs: list[float]) -> Summary:
    values = [float(v) for v in runs]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError(f"cannot summarise runs {runs!r}")
    if len(values) == 1:
        v = values[0]
        return Summary(v, v, v, None, 1)
    p25, _, p75 = statistics.quantiles(values, n=4, method="inclusive")
    mean = statistics.fmean(values)
    cv = statistics.stdev(values) / mean if mean else None
    return Summary(statistics.median(values), p25, p75, cv, len(values))


def _runs(case: dict, metric: str) -> list[float] | None:
    block = (case.get("metrics") or {}).get(metric)
    if block and block.get("runs"):
        return block["runs"]
    if metric == "timeNs":
        return case.get("nanosPerOperation")
    return None


def read_prepared(prepared_yaml: Path | None) -> dict[str, dict]:
    """Prepared cases by id; empty when preparation's file is absent."""
    if prepared_yaml is None:
        return {}
    doc = read_yaml(prepared_yaml)
    return {c["id"]: c for c in doc.get("cases") or []}


def read_results(benchmark_json: Path, prepared: dict[str, dict] | None = None
                 ) -> tuple[list[PrimitiveRow], Measurements]:
    """Cases with no timing samples are not rows; run_log reports them."""
    doc = json.loads(Path(benchmark_json).read_text())
    prepared = prepared or {}
    rows: list[PrimitiveRow] = []
    measurements: Measurements = {}
    for c in doc.get("cases") or []:
        time_runs = _runs(c, "timeNs")
        if not time_runs:
            continue
        plan = prepared.get(c["id"]) or {}
        rows.append(PrimitiveRow(
            rowId=c["id"], type=c["type"], algorithm=c["algorithm"], provider=c["provider"],
            operation=c["operation"], keySize=c.get("keySize"), inputSize=c.get("inputSize"),
            phase=plan.get("phase"),
            keyKind=(plan.get("key") or {}).get("kind") or c.get("keyKind"),
        ))
        alloc_runs = _runs(c, "allocationCount")
        measurements[c["id"]] = {"timeNs": summarise(time_runs),
                                 "allocations": summarise(alloc_runs) if alloc_runs else None}
    return rows, measurements


def comparability(runtime: dict, processes: int) -> list[str]:
    """Reasons these numbers may not transfer to another run, from the run's own runtime block."""
    notes = []
    if str(runtime.get("cpuLocked", "")).lower() != "true":
        notes.append("cpu_not_locked: clocks were free to scale; ratios between cases are noisier than they look")
    if str(runtime.get("sustainedPerformanceModeEnabled", "")).lower() != "true":
        notes.append("sustained_performance_off: thermal state may drift across the run")
    sleep = runtime.get("thermalThrottleSleepSeconds")
    if sleep not in (None, "", "0", 0):
        notes.append(f"thermal_throttle: the device paused {sleep}s mid-run")
    if processes < 2:
        notes.append("single_process: variance across processes (JIT, heap layout) is not in these numbers")
    return notes
