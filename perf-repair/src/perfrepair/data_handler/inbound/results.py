from __future__ import annotations

from ...files import read_yaml

import json
import math
import statistics
from dataclasses import replace
from pathlib import Path


from ...dto import PrimitiveRow, Summary
from ...dto.metrics import METRICS
from .bootstrap import median_interval

Measurements = dict[str, dict[str, Summary]]


def summarise(processes: list[list[float]]) -> Summary:
    """One metric of one case; each process's runs stay apart so the interval resamples them as units."""
    kept = tuple(tuple(float(v) for v in runs) for runs in processes if runs)
    values = [v for runs in kept for v in runs]
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError(f"cannot summarise runs {processes!r}")
    if len(values) == 1:
        v = values[0]
        return Summary(v, v, v, None, 1, None, None, kept)
    p25, _, p75 = statistics.quantiles(values, n=4, method="inclusive")
    mean = statistics.fmean(values)
    cv = statistics.stdev(values) / mean if mean else None
    return Summary(statistics.median(values), p25, p75, cv, len(values), *median_interval(kept), kept)


def _runs(case: dict, metric: str) -> list[float] | None:
    block = (case.get("metrics") or {}).get(metric)
    return block["runs"] if block and block.get("runs") else None


def _processes(case: dict, metric: str, per_process: list[dict[str, dict]]) -> list[list[float]] | None:
    merged = _runs(case, metric)
    if not merged or not per_process:
        return [merged] if merged else None
    parts = [runs for doc in per_process if (runs := _runs(doc.get(case["id"]) or {}, metric))]
    if sorted(v for runs in parts for v in runs) != sorted(merged):
        raise ValueError(f"{case['id']}.{metric}: the process files hold {sum(map(len, parts))} runs that are not "
                         f"the {len(merged)} runs of the merged benchmark.json")
    return parts


def _summaries(case: dict, per_process: list[dict[str, dict]]) -> dict[str, Summary]:
    """Every registry metric with runs; one without is absent. A kind-less block predates its kinds: the first one."""
    out = {}
    for metric in METRICS:
        runs = _processes(case, metric.name, per_process)
        if runs:
            kind = case["metrics"][metric.name].get("kind", metric.kinds[0]) if metric.kinds else None
            out[metric.name] = replace(summarise(runs), kind=kind)
    return out


def read_prepared(prepared_yaml: Path | None) -> dict[str, dict]:
    if prepared_yaml is None:
        return {}
    doc = read_yaml(prepared_yaml)
    return {c["id"]: c for c in doc.get("cases") or []}


def read_results(benchmark_json: Path, prepared: dict[str, dict] | None = None, process_files: list[Path] = ()
                 ) -> tuple[list[PrimitiveRow], Measurements, dict[str, dict]]:
    """`process_files`: the per-process files the merged benchmark.json concatenates; they restore the process index.
    The third value: each case with no runs of a required metric, by id, left out of the rows; the stage decides."""
    doc = json.loads(Path(benchmark_json).read_text())
    prepared = prepared or {}
    per_process = [{c["id"]: c for c in json.loads(Path(p).read_text()).get("cases") or []} for p in process_files]
    rows: list[PrimitiveRow] = []
    measurements: Measurements = {}
    lacking: dict[str, dict] = {}
    for c in doc.get("cases") or []:
        summaries = _summaries(c, per_process)
        if any(m.required and m.name not in summaries for m in METRICS):
            lacking[c["id"]] = c
            continue
        plan = prepared.get(c["id"]) or {}
        rows.append(PrimitiveRow(
            rowId=c["id"], type=c["type"], algorithm=c["algorithm"], provider=c["provider"],
            operation=c["operation"], keySize=c.get("keySize"), inputSize=c.get("inputSize"),
            phase=plan.get("phase"),
            keyKind=(plan.get("key") or {}).get("kind") or c.get("keyKind"),
            parameters=c.get("parameters"),
        ))
        measurements[c["id"]] = summaries
    return rows, measurements, lacking


def thermal_of(cases: list[dict]) -> dict[str, dict]:
    """Per case its temperatures and thermal pause as measured; nothing for a case without them."""
    out = {}
    for c in cases:
        kept = {k: c[k] for k in ("thermal", "thermalThrottleSleepSeconds") if c.get(k) is not None}
        if kept:
            out[c["id"]] = kept
    return out


def ended_throttled(thermal: dict[str, dict]) -> list[str]:
    return sorted(c for c, t in thermal.items() if ((t.get("thermal") or {}).get("endStatus") or 0) > 0)


def comparability(runtime: dict, processes: int) -> list[str]:
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
