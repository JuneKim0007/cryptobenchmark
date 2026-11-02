"""The dossier step: scopes + groups + measurements → apps/<app>/dossiers.json, validated before writing."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto.site import Scope
from ..files import read_json, write_json
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..validation.grouping.output import read_groups
from ..result.dossier import build_dossiers
from ..validation import require, validate_measurements
from ..validation.dossiers import validate_dossiers


def dossier(run: Path, app: str, source: Path, catalog: Catalog, echo=print) -> dict:
    rows, measurements = rd.load_rows(run), rd.load_measurements(run)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    grouping = GroupingPaths(run)
    catalog.require_same(rd.load_screen_catalog(grouping))
    groups = read_groups(grouping)
    paths = rd.AppPaths(run, app)
    scopes = [Scope.from_json(s) for s in read_json(paths.scopes)["scopes"]]
    facts = read_json(paths.facts)
    verdicts = catalog.handler().app_verdicts(groups, rd.load_screen(grouping), facts.get("targetSdk"))
    doc = build_dossiers(app, scopes, facts, groups, rows, measurements.byRow, source, verdicts)
    require(rd.DOSSIERS, validate_dossiers(doc, scopes, groups, verdicts))
    write_json(paths.dossiers, doc)
    echo(f"{app}: {len(doc['dossiers'])} dossiers, {len(doc['noOptions'])} scopes without options")
    return doc
