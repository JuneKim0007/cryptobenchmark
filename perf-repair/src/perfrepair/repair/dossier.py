"""The dossier step: scopes + groups + measurements → <app>/dossiers.json, validated before writing."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .. import run_dir as rd
from ..dto.perf_mode import NO_EVIDENCE, PerfMode
from ..dto.site import Scope, reason_code
from ..dto.unit import read_units
from ..files import read_json, write_json
from ..log import step
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..validation.grouping.output import read_groups
from ..result.dossier import build_dossiers
from ..result.unit_dossiers import by_unit
from ..validation import require, validate_measurements
from ..validation.dossier_units import validate_dossier_units
from ..validation.dossiers import validate_dossiers


def dossier(run: Path, app: str, source: Path, catalog: Catalog, perf: PerfMode, echo=print) -> dict:
    rows, measurements = rd.load_rows(run), rd.load_measurements(run)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    grouping = GroupingPaths(run)
    catalog.require_same(rd.load_screen_catalog(grouping))
    groups = read_groups(grouping)
    paths = rd.AppPaths(run, app)
    scopes = [Scope.from_json(s) for s in read_json(paths.scopes)["scopes"]]
    units = read_units(read_json(paths.units))
    facts = read_json(paths.facts)
    verdicts = catalog.handler().app_verdicts(groups, rd.load_screen(grouping), facts.get("targetSdk"))
    with step("repair", "dossier", app=app) as s:
        doc = by_unit(build_dossiers(app, scopes, facts, groups, rows, measurements.byRow, source, verdicts, perf), units,
                     scopes, groups)
        require(rd.DOSSIERS, validate_dossiers(doc, scopes, groups, verdicts) + validate_dossier_units(doc, units, scopes, groups))
        write_json(paths.dossiers, doc)
        s.count(scopes=len(scopes), units=len(doc["units"]), dossiers=len(doc["dossiers"]), options=sum(len(d["options"]) for d in doc["dossiers"]),
                noOptions=dict(Counter(n["reason"] for n in doc["noOptions"])),
                noEvidence=sum(reason_code(n["reason"]) == NO_EVIDENCE for n in doc["noOptions"]))
        s.wrote(paths.dossiers)
    echo(f"{app}: {len(doc['dossiers'])} dossiers, {len(doc['noOptions'])} scopes without options")
    return doc
