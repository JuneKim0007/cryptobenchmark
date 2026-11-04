"""validate_run: the stage replay over a device folder; every artifact present checked, each by its validator."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..files import read_json
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog
from ..validation.grouping.output import read_groups
from ..validation.app import validate_app_dir
from ..validation.failure import ValidationFailed
from ..validation.grouping.interop import validate_interop
from ..validation.report import validate_report
from ..validation.summary import validate_summary
from ..validation.rows import validate_rows
from .apps import check_dossiers
from .device import (check_beside_rows, check_charters, check_events, check_primitives, check_suggestions, check_used,
                     parsed)
from .grouping import check_grouping, check_screen, check_worthiness


def validate_run(run: Path, catalog: Catalog) -> dict[str, list[str]]:
    run, out = Path(run), {}
    if not (run / rd.ROWS).is_file():
        return {rd.ROWS: [f"missing: {run / rd.ROWS}"]}
    rows = parsed(rd.load_rows, run)
    if isinstance(rows, str):
        return {rd.ROWS: [rows]}
    out[rd.ROWS] = validate_rows(rows)
    out |= check_beside_rows(run, rows)
    out |= check_charters(run) | check_events(run) | check_suggestions(run)
    reports = []
    for directory in rd.app_dirs(run):
        out |= validate_app_dir(directory)
        if (directory / rd.REPORT).is_file():
            reports.append(read_json(directory / rd.REPORT))
            out[f"{directory.name}/{rd.REPORT}"] = validate_report(reports[-1], directory.name)
    if (run / rd.SUMMARY).is_file():
        out[rd.SUMMARY] = validate_summary(read_json(run / rd.SUMMARY), reports)
    grouping = GroupingPaths(run)
    if grouping.items.exists():
        out["grouping"] = check_grouping(grouping)
        out |= check_screen(grouping, catalog) | check_used(run, grouping)
    out |= check_primitives(run, rows)
    if not grouping.groups.exists():
        return out
    try:
        groups = read_groups(grouping)
        out["grouping/groups.json"] = []
    except ValidationFailed as e:
        out["grouping/groups.json"] = e.problems
        return out
    out |= validate_interop(groups, grouping.interop_plan, grouping.interop)
    screen = rd.load_screen(grouping)
    out |= check_dossiers(run, groups, screen, catalog)
    for name in rd.worthiness_modes(run):
        out[rd.worthiness(run, name).name] = check_worthiness(run, name, groups, rows, screen)
    return out
