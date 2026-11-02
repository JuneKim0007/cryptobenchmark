"""python3 -m perfrepair.data_handler.inbound — a results manifest → rows, measurements, run log; apps: perfrepair.app."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ... import run_dir as rd
from ...dto import Measurements
from ...failure import reported
from ...files import write_json
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
    ap = argparse.ArgumentParser(prog="perfrepair.data_handler.inbound", description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True, help="a cryptobenchmark results/manifest.yaml")
    ap.add_argument("-o", "--out", type=Path, required=True, help="run directory to write into")
    a = ap.parse_args(argv)
    return reported(lambda: _inbound(ap, a))


def _inbound(ap: argparse.ArgumentParser, a: argparse.Namespace) -> None:
    manifest, base = read_manifest(a.manifest)
    require(str(a.manifest), validate_manifest(manifest, base))
    benchmark = manifest_file(manifest, base, "benchmark")
    if benchmark is None:
        ap.error(f"{a.manifest}: no benchmark file; the run measured nothing")
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

    a.out.mkdir(parents=True, exist_ok=True)
    write_json(a.out / rd.ROWS, {"schemaVersion": SCHEMA_VERSION, "rows": [r.to_json() for r in rows]})
    write_json(a.out / rd.MEASUREMENTS, summaries.to_json())
    write_json(a.out / rd.RUN_LOG, log.to_json())

    print(f"{a.out}: {len(rows)} rows, {len(log.entries)} log entries from {raw} records")
    for note in notes:
        print(f"  warning {note}")


if __name__ == "__main__":
    sys.exit(main())
