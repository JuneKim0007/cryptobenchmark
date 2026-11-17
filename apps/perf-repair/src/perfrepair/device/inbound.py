"""The inbound stage: a device's manifest → rows, measurements, run log beside it, validated before writing."""
from __future__ import annotations

from pathlib import Path

from cryptobench.shared.paths import RunTree
from cryptobench.shared.paths import MEASUREMENTS, ROWS, RUN_LOG
from ..data_handler.inbound import build_run_log, comparability, manifest_file, read_manifest, read_prepared, read_results
from ..data_handler.inbound.results import ended_throttled, thermal_of
from ..dto import Measurements
from ..dto.pattern import VARIANTS
from ..dto.primitive import ROWS_SCHEMA_VERSION
from cryptobench.shared.paths import VARIANTS as MEASURED_VARIANTS
from ..files import read_json
from cryptobench.shared.document.json_dump import write_json
from cryptobench.shared.log.emit import step
from cryptobench.shared.errors.validation import require
from ..validation import validate_manifest, validate_measurements, validate_rows, validate_run_log
from cryptobench.shared.stop.terminate import terminate
from cryptobench.shared.errors.input_error import InputError


def write_inbound(device: Path) -> list[str]:
    """The lines to print: a count, then each comparability warning."""
    with step("inbound", "inbound") as s:
        lines, counts = _write_inbound(device)
        s.count(**counts)
        s.wrote(*(Path(device) / name for name in (ROWS, MEASUREMENTS, RUN_LOG)))
    return lines


def unrepaired_left_out(rows: list, measurements: dict) -> tuple[list, dict, list]:
    """A row on a path the benchmark measures but no call site pattern maps to (secure) is variant_unrepaired: skip leaves it out,
    named in the run log; an unknown variant stays for validate_rows to refuse."""
    unrepaired = [r for r in rows if r.variant in MEASURED_VARIANTS and r.variant not in VARIANTS]
    if not unrepaired:
        return rows, measurements, []
    ids = sorted(r.rowId for r in unrepaired)
    terminate("variant_unrepaired", f"{len(ids)} cases measure {sorted({r.variant for r in unrepaired})}, a path no call site pattern maps to: "
              + ", ".join(ids), stage="inbound", step="results", data={"cases": ids})
    left = set(ids)
    return [r for r in rows if r.rowId not in left], {k: v for k, v in measurements.items() if k not in left}, unrepaired


def _write_inbound(device: Path) -> tuple[list[str], dict]:
    path = RunTree(device).manifest
    manifest, base = read_manifest(path)
    require(str(path), validate_manifest(manifest, base))
    benchmark = manifest_file(manifest, base, "benchmark")
    if benchmark is None:
        raise InputError(f"no_benchmark: {path}: the run measured nothing; run the benchmark")
    prepared = read_prepared(manifest_file(manifest, base, "prepared"))
    processes = [(base / p).resolve() for p in manifest.files.get("processes") or []]
    rows, measurements, lacking = read_results(benchmark, prepared, processes)
    if lacking:
        # skip leaves them out of the rows, counted and named in the run log under the same code
        terminate("no_required_metric", f"{len(lacking)} cases of benchmark.json have no runs of a required metric: "
                  + ", ".join(sorted(lacking)), stage="inbound", step="results", data={"cases": sorted(lacking)})
    rows, measurements, unrepaired = unrepaired_left_out(rows, measurements)
    log, raw = build_run_log(rows, prepared, manifest_file(manifest, base, "skipped"),
                             manifest_file(manifest, base, "inventory"), lacking, unrepaired)
    notes = comparability(manifest.runtime, max(1, len(processes)))
    thermal = thermal_of(read_json(benchmark).get("cases") or [])
    summaries = Measurements(manifest.runtime, notes, measurements, thermal)
    throttled = ended_throttled(thermal)
    if throttled:
        terminate("thermal_throttled_at_end", f"{len(throttled)} cases ended throttled: " + ", ".join(throttled),
                  stage="inbound", step="results", data={"cases": throttled})
    require(ROWS, validate_rows(rows))
    require(MEASUREMENTS, validate_measurements(summaries, rows))
    require(RUN_LOG, validate_run_log(log, rows))

    write_json(RunTree(device).rows, {"schemaVersion": ROWS_SCHEMA_VERSION, "rows": [r.to_json() for r in rows]})
    write_json(RunTree(device).measurements, summaries.to_json())
    write_json(RunTree(device).run_log, log.to_json())
    return [f"{device}: {len(rows)} rows, {len(log.entries)} log entries from {raw} records",
            *(f"  warning {note}" for note in notes)], {"rows": len(rows), "logEntries": len(log.entries),
                                                        "records": raw, "warnings": len(notes)}
