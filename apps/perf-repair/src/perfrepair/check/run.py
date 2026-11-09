"""validate_run: the stage replay over a device folder; every artifact present checked, each by its validator."""
from __future__ import annotations

from pathlib import Path

from cryptobench.paths import AppTree, GroupingTree, RunTree
from cryptobench.paths import APP_REPORT, ROWS, SUMMARY
from .. import run_dir as rd
from ..files import read_json
from ..screen.catalog import Catalog
from ..validation.grouping.output import read_groups
from ..validation.app import validate_app_dir
from ..validation.failure import ValidationFailed
from ..validation.grouping.interop import validate_interop
from ..validation.report import validate_report
from ..validation.summary import validate_summary
from ..validation.rows import validate_rows
from .apps import check_dossiers, check_repair
from .device import (check_beside_rows, check_charters, check_details, check_events, check_manifest, check_primitives,
                     check_suggestions, check_used, parsed)
from .grouping import check_grouping, check_screen


def validate_run(run: Path, catalog: Catalog) -> dict[str, list[str]]:
    run, out = Path(run), {}
    if not (RunTree(run).rows).is_file():
        return {ROWS: [f"missing: {RunTree(run).rows}"]}
    rows = parsed(rd.load_rows, run)
    if isinstance(rows, str):
        return {ROWS: [rows]}
    out[ROWS] = validate_rows(rows)
    out |= check_beside_rows(run, rows)
    out |= check_manifest(run) | check_details(run) | check_repair(run)
    out |= check_charters(run) | check_events(run) | check_suggestions(run)
    reports = []
    for directory in RunTree(run).apps():
        out |= validate_app_dir(directory)
        if (AppTree.at(directory).report).is_file():
            reports.append(read_json(AppTree.at(directory).report))
            out[f"{directory.name}/{APP_REPORT}"] = validate_report(reports[-1], directory.name)
    if (RunTree(run).summary).is_file():
        out[SUMMARY] = validate_summary(read_json(RunTree(run).summary), reports)
    grouping = GroupingTree(run)
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
    return out
