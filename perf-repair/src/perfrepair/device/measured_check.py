"""measured_check: each used item's planned cases against rows and measurements, one status per (item, operation,
variant, key size, input size, metric): measured, or a gap of one class with its reason (dto/benchmark_coverage.py)."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..catalog.harness_operations import operations_of
from ..data_handler.inbound import read_manifest
from ..data_handler.inbound.manifest import manifest_file
from ..dto.benchmark_coverage import (
    ANY,
    LOST,
    LOW_QUALITY,
    NEVER_PLANNED,
    NO_OPERATION,
    PARTIAL,
    REFUSED,
    REPEATS,
    Coverage,
    Gap,
)
from ..dto.grouping import parse_qualified, qualified
from ..dto.metrics import METRICS
from ..dto.perf_mode import PerfMode
from ..files import read_yaml
from ..result.estimate import MIN_RUNS

NO_HARNESS_OPERATION = "no_harness_operation: the harness times no operation of this engine type"
NOT_IN_PLAN = "not_in_plan: the selection never planned it"
REFUSING = ("skipped", "not_runnable")
ENERGY_CAPTURES = ("measured",)


def _metrics(case: dict, perf: PerfMode) -> list[str]:
    """What the case was planned to measure, of what the perfMode selects."""
    planned = set(case.get("metrics") or ("TIME",))
    capture = (((case.get("harness") or {}).get("energy") or {}).get("capture"))
    chosen = [m.name for m in METRICS if m.run in planned or (m.kinds and capture in ENERGY_CAPTURES)]
    return [m for m in chosen if m in perf.names]


class _Run:
    """The device folder's plan, rows, summaries and run log, read once."""

    def __init__(self, device: Path):
        manifest, base = read_manifest(device / rd.MANIFEST)
        prepared = manifest_file(manifest, base, "prepared")
        cases = (read_yaml(prepared).get("cases") or []) if prepared else []
        self.rows = {r.rowId: r for r in rd.load_rows(device)}
        self.summaries = rd.load_measurements(device).byRow
        log = rd.load_run_log(device).entries
        self.refused_case = {i: e.reason or e.status for e in log if e.status == "skipped" for i in e.rowIds}
        self.lost_case = {i: e.reason or e.status for e in log if e.status == "unmeasured" for i in e.rowIds}
        self.refused_item = {qualified(e.type, e.algorithm, e.provider): e.reason or e.status for e in log
                             if e.status in REFUSING and e.type and e.algorithm and e.provider}
        self.planned: dict[str, list[dict]] = {}
        for c in cases:
            self.planned.setdefault(qualified(c["type"], c["algorithm"], c["provider"]), []).append(c)


def _case_gaps(run: _Run, item: str, case: dict, metrics: list[str], lost_before: set) -> tuple[int, list[Gap]]:
    cid = case["id"]
    row = run.rows.get(cid)
    shape = (item, row.operation if row else case.get("operation") or ANY, case.get("variant") or ANY,
             row.keySize if row else case.get("keySize"), row.inputSize if row else case.get("inputSize"))
    measured, gaps = 0, []
    for metric in metrics:
        summary = (run.summaries.get(cid) or {}).get(metric)
        if summary and summary.n >= MIN_RUNS:
            measured += 1
            continue
        if summary:
            cls, why = LOW_QUALITY, f"too_few_runs: {summary.n} runs, the estimate needs {MIN_RUNS}"
        elif row:
            cls, why = PARTIAL, f"metric_missing: the case has no {metric} runs"
        elif cid in run.refused_case:
            cls, why = REFUSED, run.refused_case[cid]
        else:
            why = run.lost_case.get(cid) or "no_samples: planned, absent from benchmark.json"
            cls = REPEATS if (*shape, metric) in lost_before else LOST
        gaps.append(Gap(*shape, metric, cls, why, cid))
    return measured, gaps


def measured_check(device: Path, used: frozenset[str], perf: PerfMode, lost_before: set | None = None) -> Coverage:
    """lost_before: the keys a delta already measured again; lost a second time they repeat, and are not rerun."""
    device = Path(device)
    run, lost_before = _Run(device), lost_before or set()
    measured, gaps = 0, []
    for item in sorted(used):
        if not operations_of(parse_qualified(item)[0]):
            gaps.append(Gap(item, ANY, ANY, None, None, ANY, NO_OPERATION, NO_HARNESS_OPERATION))
            continue
        cases = run.planned.get(item)
        if not cases:
            refused = run.refused_item.get(item)
            gaps.append(Gap(item, ANY, ANY, None, None, ANY, REFUSED if refused else NEVER_PLANNED, refused or NOT_IN_PLAN))
            continue
        for case in cases:
            n, found = _case_gaps(run, item, case, _metrics(case, perf), lost_before)
            measured, gaps = measured + n, gaps + found
    return Coverage(tuple(sorted(used)), measured, tuple(gaps))
