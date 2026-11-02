"""The dossier step: scopes + groups + measurements → apps/<app>/dossiers.json, validated before writing."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto.site import Scope
from ..files import read_json, write_json
from ..run_dir import GroupingPaths
from ..validation.grouping.output import read_groups
from ..result.dossier import build_dossiers
from ..validation import require, validate_measurements
from ..validation.dossiers import validate_dossiers


def dossier(run: Path, app: str, source: Path, echo=print) -> dict:
    rows, measurements = rd.load_rows(run), rd.load_measurements(run)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    groups = read_groups(GroupingPaths(run))
    paths = rd.AppPaths(run, app)
    scopes = [Scope.from_json(s) for s in read_json(paths.scopes)["scopes"]]
    doc = build_dossiers(app, scopes, read_json(paths.facts), groups, rows, measurements.byRow, source)
    require(rd.DOSSIERS, validate_dossiers(doc, scopes, groups))
    write_json(paths.dossiers, doc)
    echo(f"{app}: {len(doc['dossiers'])} dossiers, {len(doc['noOptions'])} scopes without options")
    return doc
