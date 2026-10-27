"""python3 -m perfrepair.result dossier --run <run> --app <name> --source <app root> — after scope and grouping."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .. import run_dir as rd
from ..dto.site import Scope
from ..files import read_json, write_json
from ..grouping.paths import GroupingPaths
from ..grouping.report.checks import read_groups
from ..validation import require, validate_measurements
from ..validation.dossiers import validate_dossiers
from .dossier import build_dossiers


def dossier(run: Path, app: str, source: Path, echo=print) -> dict:
    rows, measurements = rd.load_rows(run), rd.load_measurements(run)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    groups = read_groups(GroupingPaths(run))
    directory = rd.app(run, app)
    scopes = [Scope.from_json(s) for s in read_json(directory / rd.SCOPES)["scopes"]]
    doc = build_dossiers(app, scopes, read_json(directory / rd.APP), groups, rows, measurements.byRow, source)
    require(rd.DOSSIERS, validate_dossiers(doc, scopes, groups))
    write_json(directory / rd.DOSSIERS, doc)
    echo(f"{app}: {len(doc['dossiers'])} dossiers, {len(doc['noOptions'])} scopes without options")
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="perfrepair.result", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("dossier")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--app", required=True, help="the app's name under <run>/apps/")
    p.add_argument("--source", type=Path, required=True, help="the app's source root; scope files are relative to it")
    a = ap.parse_args(argv)
    dossier(a.run, a.app, a.source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
