"""python3 -m perfrepair.app — an app's source → <device>/<path id>/sites.json, app.json, scopes.json per project root, validated before writing."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import run_dir as rd
from ..catalog.names import NamesError
from ..config.args import add_config_arg
from ..config.device_results import add_device_results_arg, fill_device_results
from ..data_handler.inbound import RunContext
from ..failure import reported
from ..files import write_json
from ..log import log_to_stderr
from ..scope.build import build_scopes
from ..validation import require, validate_manifest
from ..validation.app import validate_app_facts, validate_scopes
from .app_facts import app_facts
from .dependencies import bundled, read_libraries
from .detect import Detection, detect
from .gate import AppRoot, GateError, open_apps
from .path_id import path_id, unit_id
from .sdk import sdk_levels
from .sources import build_files

SCHEMA_VERSION = 1


def main(argv: list[str] | None = None) -> int:
    log_to_stderr()
    ap = argparse.ArgumentParser(prog="perfrepair.app", description=__doc__)
    add_device_results_arg(ap)
    add_config_arg(ap)
    ap.add_argument("--app", type=Path, required=True, help="the app's source folder; read only; its path gives the app's id "
                                                            "and, with several project roots, one <id>.<root dirs joined by '.'> each")
    a = ap.parse_args(argv)
    return reported(lambda: _app(ap, a))


def _app(ap: argparse.ArgumentParser, a: argparse.Namespace) -> int:
    fill_device_results(ap, a)
    manifest = a.device_results / rd.MANIFEST
    context = RunContext.load(manifest)
    require(str(manifest), validate_manifest(context.manifest, context.base))
    if context.file("probe") is None:
        ap.error(f"{manifest}: no probe file; detection needs it for engine types and aliases")
    try:
        apps = open_apps(a.app)
    except GateError as e:
        print(f"error {e}", file=sys.stderr)
        return 2
    pid = path_id(a.app)
    units = {pid: apps[0]} if len(apps) == 1 else {unit_id(pid, app.projectRoot): app for app in apps}
    if len(units) != len(apps):
        ap.error(f"{a.app}: project roots {[app.projectRoot for app in apps]} collide as unit names")
    try:
        dirs = {name: rd.app_dir(a.device_results, name) for name in units}
    except ValueError as e:
        ap.error(str(e))
    probe, names = context.probe, context.names
    try:
        found = {name: detect(app, probe, names, context.manifest.providers) for name, app in units.items()}
    except NamesError as e:
        print(f"error {e}", file=sys.stderr)
        return 2
    for name, app in units.items():
        write_unit(name, pid, app, dirs[name], found[name])
    return 0


def write_unit(name: str, pid: str, app: AppRoot, out_dir: Path, found: Detection) -> None:
    builds = build_files(app.path)
    facts = app_facts(name, pid, app.path, app.projectRoot, bundled(builds, read_libraries()), found.registers,
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
