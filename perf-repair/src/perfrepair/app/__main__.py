"""python3 -m perfrepair.app — an app's source → apps/<unit>/sites.json, app.json, scopes.json per project root, validated before writing."""
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
from .gate import AppRoot, GateError, open_apps
from .sdk import sdk_levels
from .sources import build_files

SCHEMA_VERSION = 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.app", description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True, help="a cryptobenchmark results/manifest.yaml")
    ap.add_argument("--app", type=Path, required=True, help="the app's source folder; read only")
    ap.add_argument("--run", type=Path, required=True, help="run directory to write into")
    ap.add_argument("--name", required=True, help="the app's folder under <run>/apps/; with several project roots, "
                                                "one <name>.<root dirs joined by '.'> each")
    a = ap.parse_args(argv)

    try:
        rd.app_dir(a.run, a.name)
    except ValueError as e:
        ap.error(str(e))
    manifest, base = read_manifest(a.manifest)
    require(str(a.manifest), validate_manifest(manifest, base))
    probe = manifest_file(manifest, base, "probe")
    if probe is None:
        ap.error(f"{a.manifest}: no probe file; detection needs it for engine types and aliases")
    try:
        apps = open_apps(a.app)
    except GateError as e:
        print(f"error {e}", file=sys.stderr)
        return 2
    units = {a.name: apps[0]} if len(apps) == 1 else {unit_name(a.name, app.projectRoot): app for app in apps}
    if len(units) != len(apps):
        ap.error(f"{a.app}: project roots {[app.projectRoot for app in apps]} collide as unit names")
    try:
        dirs = {name: rd.app_dir(a.run, name) for name in units}
    except ValueError as e:
        ap.error(str(e))
    index = read_probe_index(probe)
    for name, app in units.items():
        write_unit(name, app, dirs[name], index, manifest.providers)
    return 0


def unit_name(name: str, project_root: str) -> str:
    return ".".join([name, *project_root.split("/")])


def write_unit(name: str, app: AppRoot, out_dir: Path, index, providers) -> None:
    found = detect(app, index, providers)
    builds = build_files(app.path)
    facts = app_facts(name, app.path, app.projectRoot, bundled(builds, read_libraries()), found.registers,
                      sdk_levels(builds))
    scoping = build_scopes(name, app.path, found.sites)
    scopes = scoping.document(name)
    require(rd.APP, validate_app_facts(facts))
    require(rd.SCOPES, validate_scopes(scopes))

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / rd.SITES, {"schemaVersion": SCHEMA_VERSION, "app": name, "root": str(app.path),
                                    "sites": found.sites, "dropped": found.dropped})
    write_json(out_dir / rd.APP, facts)
    write_json(out_dir / rd.SCOPES, scopes)
    print(f"{out_dir}: {len(found.sites)} sites in {found.files} files ({found.testFiles} test files not scanned), "
          f"{len(found.dropped)} dropped by import, {found.folded} folded from constants, "
          f"{len(scoping.scopes)} scopes, {len(scoping.unscoped)} without a function")

if __name__ == "__main__":
    sys.exit(main())
