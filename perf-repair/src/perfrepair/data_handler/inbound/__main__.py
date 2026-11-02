"""python3 -m perfrepair.data_handler.inbound — a device's manifest → rows, measurements, run log beside it."""
from __future__ import annotations

import argparse
import sys

from ... import run_dir as rd
from ...config.args import add_config_arg
from ...config.device_results import add_device_results_arg, fill_device_results
from ...dto import Measurements
from ...failure import reported
from ...files import write_json
from ...log import log_to_stderr
from ...validation import require, validate_manifest, validate_measurements, validate_rows, validate_run_log
from . import (
    build_run_log,
    comparability,
    manifest_file,
    read_manifest,
    read_prepared,
    read_results,
)

SCHEMA_VERSION = 1


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap = argparse.ArgumentParser(prog="perfrepair.data_handler.inbound", description=__doc__)
    add_device_results_arg(ap)
    add_config_arg(ap)
    a = ap.parse_args(argv)
    return reported(lambda: _inbound(ap, a))


def _inbound(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    fill_device_results(ap, a)
    path = a.device_results / rd.MANIFEST
    manifest, base = read_manifest(path)
    require(str(path), validate_manifest(manifest, base))
    benchmark = manifest_file(manifest, base, "benchmark")
    if benchmark is None:
        ap.error(f"{path}: no benchmark file; the run measured nothing")
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

    write_json(a.device_results / rd.ROWS, {"schemaVersion": SCHEMA_VERSION, "rows": [r.to_json() for r in rows]})
    write_json(a.device_results / rd.MEASUREMENTS, summaries.to_json())
    write_json(a.device_results / rd.RUN_LOG, log.to_json())

    print(f"{a.device_results}: {len(rows)} rows, {len(log.entries)} log entries from {raw} records")
    for note in notes:
        print(f"  warning {note}")


if __name__ == "__main__":
    sys.exit(main())
