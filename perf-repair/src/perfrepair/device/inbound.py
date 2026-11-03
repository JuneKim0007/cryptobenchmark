"""The inbound stage: a device's manifest → rows, measurements, run log beside it, validated before writing."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..data_handler.inbound import build_run_log, comparability, manifest_file, read_manifest, read_prepared, read_results
from ..dto import Measurements
from ..files import write_json
from ..log import step
from ..validation import require, validate_manifest, validate_measurements, validate_rows, validate_run_log
from ..stop.halt import Coded

SCHEMA_VERSION = 1


def write_inbound(device: Path) -> list[str]:
    """The lines to print: a count, then each comparability warning."""
    with step("inbound", "inbound") as s:
        lines, counts = _write_inbound(device)
        s.count(**counts)
        s.wrote(*(Path(device) / name for name in (rd.ROWS, rd.MEASUREMENTS, rd.RUN_LOG)))
    return lines


def _write_inbound(device: Path) -> tuple[list[str], dict]:
    path = Path(device) / rd.MANIFEST
    manifest, base = read_manifest(path)
    require(str(path), validate_manifest(manifest, base))
    benchmark = manifest_file(manifest, base, "benchmark")
    if benchmark is None:
        raise Coded(f"no_benchmark: {path}: the run measured nothing; run the benchmark")
    prepared = read_prepared(manifest_file(manifest, base, "prepared"))
    processes = [(base / p).resolve() for p in manifest.files.get("processes") or []]
    rows, measurements = read_results(benchmark, prepared, processes)
    log, raw = build_run_log(rows, prepared, manifest_file(manifest, base, "skipped"),
                             manifest_file(manifest, base, "inventory"))
    notes = comparability(manifest.runtime, max(1, len(processes)))
    summaries = Measurements(manifest.runtime, notes, measurements)
    require(rd.ROWS, validate_rows(rows))
    require(rd.MEASUREMENTS, validate_measurements(summaries, rows))
    require(rd.RUN_LOG, validate_run_log(log, rows))

    write_json(Path(device) / rd.ROWS, {"schemaVersion": SCHEMA_VERSION, "rows": [r.to_json() for r in rows]})
    write_json(Path(device) / rd.MEASUREMENTS, summaries.to_json())
    write_json(Path(device) / rd.RUN_LOG, log.to_json())
    return [f"{device}: {len(rows)} rows, {len(log.entries)} log entries from {raw} records",
            *(f"  warning {note}" for note in notes)], {"rows": len(rows), "logEntries": len(log.entries),
                                                        "records": raw, "warnings": len(notes)}
