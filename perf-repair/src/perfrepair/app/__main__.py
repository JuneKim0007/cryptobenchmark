"""python3 -m perfrepair.app — an app's source → <device>/<path id>/sites.json, app.json, scopes.json per project root, validated before writing."""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from .. import run_dir as rd
from ..catalog.names import Names, NamesError
from ..config.args import add_config_arg
from ..dto.site import NOT_ON_DEVICE, NOT_ON_DEVICE_STEP
from ..config.device_results import add_device_results_arg, fill_device_results
from ..failure import reported
from ..files import write_json
from ..log import attach, step
from ..scope.build import Scoping, build_scopes
from ..scope.units.build import build_units, unit_counts, units_document
from ..validation import require, validate_manifest
from ..validation.app import validate_app_facts, validate_scopes
from ..validation.units import validate_units
from .facts.app_facts import app_facts
from .facts.dependencies import bundled, read_libraries
from .detect import Detection, detect
from .resolve import Primitives
from .facts.gate import AppRoot, GateError, open_apps
from .facts.path_id import path_id, unit_id
from .facts.sdk import sdk_levels
from .find.sources import build_files

SCHEMA_VERSION = 1


def main(argv: list[str] | None = None) -> int:
    attach()
    ap = argparse.ArgumentParser(prog="perfrepair.app", description=__doc__)
    add_device_results_arg(ap)
    add_config_arg(ap)
    ap.add_argument("--app", type=Path, required=True, help="the app's source folder; read only; its path gives the app's id "
                                                            "and, with several project roots, one <id>.<root dirs joined by '.'> each")
    a = ap.parse_args(argv)
    return reported(lambda: _app(ap, a))


def _app(ap: argparse.ArgumentParser, a: argparse.Namespace) -> int:
    fill_device_results(ap, a)
    attach(a.device_results)
    primitives = Primitives.load(a.device_results)
    require(str(primitives.context.path), validate_manifest(primitives.context.manifest, primitives.context.base))
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
    try:
        # the packaged catalog, not the probe: a site of an engine type the device lacks is still found
        engine_types = Names.load().engine_types
        found = {name: _detected(name, app, engine_types, primitives) for name, app in units.items()}
    except NamesError as e:
        print(f"error {e}", file=sys.stderr)
        return 2
    for name, app in units.items():
        write_unit(name, pid, app, dirs[name], found[name])
    return 0


def _detected(name: str, app: AppRoot, engine_types, primitives: Primitives) -> Detection:
    with step("app", "detect", app=name) as s:
        found = detect(app, engine_types, primitives.resolve)
        s.count(sites=len(found.sites), files=found.files, testFiles=found.testFiles, dropped=len(found.dropped),
                folded=found.folded, resolution=dict(Counter(site["resolution"] for site in found.sites)))
    return found


def write_unit(name: str, pid: str, app: AppRoot, out_dir: Path, found: Detection) -> None:
    builds = build_files(app.path)
    facts = app_facts(name, pid, app.path, app.projectRoot, bundled(builds, read_libraries()), found.registers,
                      sdk_levels(builds))
    with step("app", "scope", app=name) as s:
        scoping = build_scopes(name, app.path, found.sites)
        scopes = scoping.document(name)
        require(rd.APP, validate_app_facts(facts))
        require(rd.SCOPES, validate_scopes(scopes, scoping.lines))

        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / rd.SITES, {"schemaVersion": SCHEMA_VERSION, "app": name, "root": str(app.path),
                                        "sites": found.sites, "dropped": found.dropped})
        write_json(out_dir / rd.APP, facts)
        write_json(out_dir / rd.SCOPES, scopes)
        s.count(scopes=len(scoping.scopes), unscoped=len(scoping.unscoped), lifecycle=scoping.statuses())
        s.wrote(out_dir / rd.SITES, out_dir / rd.APP, out_dir / rd.SCOPES)
    print(f"{out_dir}: {len(found.sites)} sites in {found.files} files ({found.testFiles} test files not scanned), "
          f"{len(found.dropped)} dropped by import, {found.folded} folded from constants, "
          f"{len(scoping.scopes)} scopes, {len(scoping.unscoped)} without a function; lifecycle "
          + (", ".join(f"{k} {n}" for k, n in scoping.statuses().items()) or "none"))
    if any(s.lifecycle is not None and "parser_missing" in s.lifecycle.reasons for s in scoping.scopes):
        print("lifecycle unsupported: parser_missing; install the scope extra: pip install -e 'perf-repair[scope]'")
    for missing, n in sorted(Counter(s["missing"] for s in found.sites if s["resolution"] == NOT_ON_DEVICE).items()):
        print(f"{NOT_ON_DEVICE}: {missing} ({n} sites); {NOT_ON_DEVICE_STEP}")
    _write_units(name, app, out_dir, scoping)


def _write_units(name: str, app: AppRoot, out_dir: Path, scoping: Scoping) -> None:
    with step("app", "units", app=name) as s:
        units = build_units(name, scoping.scopes, app.path)
        doc = units_document(name, units)
        require(rd.UNITS, validate_units(doc, [x.to_json() for x in scoping.scopes]))
        write_json(out_dir / rd.UNITS, doc)
        s.count(**unit_counts(units))
        s.wrote(out_dir / rd.UNITS)

if __name__ == "__main__":
    sys.exit(main())
