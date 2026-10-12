"""python3 -m perfrepair.data_handler.inbound — a results manifest → rows, measurements, run log, sites."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ... import run_dir as rd
from ...dto import Measurements
from ...files import write_json
from ...validation import require, validate_manifest, validate_measurements, validate_rows, validate_run_log
from . import (
    build_run_log,
    comparability,
    manifest_file,
    read_manifest,
    read_prepared,
    read_probe_index,
    read_results,
    resolve,
    scan,
)

SCHEMA_VERSION = 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.data_handler.inbound", description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True, help="a cryptobenchmark results/manifest.yaml")
    ap.add_argument("--app", type=Path, help="app source root; omit to read the benchmark alone")
    ap.add_argument("-o", "--out", type=Path, required=True, help="run directory to write into")
    a = ap.parse_args(argv)

    manifest, base = read_manifest(a.manifest)
    require(str(a.manifest), validate_manifest(manifest, base))
    benchmark = manifest_file(manifest, base, "benchmark")
    if benchmark is None:
        ap.error(f"{a.manifest}: no benchmark file; the run measured nothing")
    prepared = read_prepared(manifest_file(manifest, base, "prepared"))
    rows, measurements = read_results(benchmark, prepared)
    log, raw = build_run_log(rows, prepared, manifest_file(manifest, base, "skipped"),
                             manifest_file(manifest, base, "inventory"))
    notes = comparability(manifest.runtime, max(1, len(manifest.files.get("processes") or [])))
    summaries = Measurements(manifest.runtime, notes, measurements)
    require(rd.ROWS, validate_rows(rows))
    require(rd.MEASUREMENTS, validate_measurements(summaries, rows))
    require(rd.RUN_LOG, validate_run_log(log, rows))

    a.out.mkdir(parents=True, exist_ok=True)
    write_json(a.out / rd.ROWS, {"schemaVersion": SCHEMA_VERSION, "rows": [r.to_json() for r in rows]})
    write_json(a.out / rd.MEASUREMENTS, summaries.to_json())
    write_json(a.out / rd.RUN_LOG, log.to_json())

    sites = ""
    if a.app:
        probe = manifest_file(manifest, base, "probe")
        if probe is None:
            ap.error(f"{a.manifest}: no probe file; --app needs it for engine types and aliases")
        index = read_probe_index(probe)
        resolved = [resolve(s, index, manifest.providers) for s in scan(a.app, index.engine_types)]
        write_json(a.out / rd.SITES, {"schemaVersion": SCHEMA_VERSION, "app": str(a.app), "sites": resolved})
        sites = f", {len(resolved)} sites"

    print(f"{a.out}: {len(rows)} rows, {len(log.entries)} log entries from {raw} records{sites}")
    for note in notes:
        print(f"  warning {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
