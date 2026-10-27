"""python3 -m perfrepair.app — an app's source → apps/<name>/sites.json, app.json, scopes.json, validated before writing."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import run_dir as rd
from ..data_handler.inbound import manifest_file, read_manifest, read_probe_index
from ..files import write_json
from ..scope.build import build_scopes
from ..validation import require, validate_manifest
from ..validation.app import validate_app_facts, validate_scopes
from .app_facts import app_facts
from .dependencies import bundled, read_libraries
from .detect import detect
from .gate import GateError, open_app
from .sdk import sdk_levels
from .sources import build_files

SCHEMA_VERSION = 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.app", description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True, help="a cryptobenchmark results/manifest.yaml")
    ap.add_argument("--app", type=Path, required=True, help="the app's source root; read only")
    ap.add_argument("--run", type=Path, required=True, help="run directory to write into")
    ap.add_argument("--name", required=True, help="the app's folder under <run>/apps/")
    a = ap.parse_args(argv)

    try:
        out_dir = rd.app_dir(a.run, a.name)
    except ValueError as e:
        ap.error(str(e))
    manifest, base = read_manifest(a.manifest)
    require(str(a.manifest), validate_manifest(manifest, base))
    probe = manifest_file(manifest, base, "probe")
    if probe is None:
        ap.error(f"{a.manifest}: no probe file; detection needs it for engine types and aliases")
    try:
        app = open_app(a.app)
    except GateError as e:
        print(f"error {e}", file=sys.stderr)
        return 2

    found = detect(app, read_probe_index(probe), manifest.providers)
    builds = build_files(app.path)
    facts = app_facts(a.name, app.path, bundled(builds, read_libraries()), found.registers, sdk_levels(builds))
    scoping = build_scopes(a.name, app.path, found.sites)
    scopes = scoping.document(a.name)
    require(rd.APP, validate_app_facts(facts))
    require(rd.SCOPES, validate_scopes(scopes))

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / rd.SITES, {"schemaVersion": SCHEMA_VERSION, "app": a.name, "root": str(app.path),
                                    "sites": found.sites, "dropped": found.dropped})
    write_json(out_dir / rd.APP, facts)
    write_json(out_dir / rd.SCOPES, scopes)
    print(f"{out_dir}: {len(found.sites)} sites in {found.files} files ({found.testFiles} test files not scanned), "
          f"{len(found.dropped)} dropped by import, {found.folded} folded from constants, "
          f"{len(scoping.scopes)} scopes, {len(scoping.unscoped)} without a function")
    return 0


if __name__ == "__main__":
    sys.exit(main())
