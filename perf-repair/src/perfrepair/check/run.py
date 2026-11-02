from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto import Verdicts
from ..dto.grouping import read_items
from ..dto.screen import Verdict, qualified_verdicts
from ..dto.grouping_state import Knowledge
from ..dto.site import Scope
from ..files import read_json
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..run_dir import GroupingPaths
from ..screen.catalog import Catalog, screening_catalog
from ..validation.grouping.output import read_groups
from ..ai.evaluate.worthiness.kind import WorthinessKind
from ..ai.runtime.engine.outbox import OutboxError, active_outbox
from ..result.evidence import build_evidence
from ..result.modes import MODES
from ..validation.dossiers import validate_dossiers
from ..validation.app import validate_app_dir
from ..validation.failure import ValidationFailed
from ..validation.grouping.interop import validate_interop
from ..validation.measurements import validate_measurements
from ..validation.report import validate_report, validate_summary
from ..validation.rows import validate_rows
from ..validation.run_log import validate_run_log
from ..validation.screen import validate_screen_document


def validate_run(run: Path, catalog: Catalog | None = None) -> dict[str, list[str]]:
    run, out = Path(run), {}
    if not (run / rd.ROWS).is_file():
        return {rd.ROWS: [f"missing: {run / rd.ROWS}"]}
    rows = rd.load_rows(run)
    out[rd.ROWS] = validate_rows(rows)
    if (run / rd.MEASUREMENTS).exists():
        out[rd.MEASUREMENTS] = validate_measurements(rd.load_measurements(run), rows)
    if (run / rd.RUN_LOG).exists():
        out[rd.RUN_LOG] = validate_run_log(rd.load_run_log(run), rows)
    reports = []
    for directory in rd.app_dirs(run):
        out |= validate_app_dir(directory)
        if (directory / rd.REPORT).is_file():
            reports.append(read_json(directory / rd.REPORT))
            out[f"{rd.APPS}/{directory.name}/{rd.REPORT}"] = validate_report(reports[-1], directory.name)
    if (run / rd.APPS / rd.SUMMARY).is_file():
        out[f"{rd.APPS}/{rd.SUMMARY}"] = validate_summary(read_json(run / rd.APPS / rd.SUMMARY), reports)
    grouping = GroupingPaths(run)
    catalog = catalog or screening_catalog(None)
    if grouping.items.exists():
        out["grouping"] = _grouping(grouping)
        out |= _screen(grouping, catalog)
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
    out |= _dossiers(run, groups, screen, catalog)
    for mode in MODES.values():
        directory = rd.worthiness(run, mode.name)
        if (directory / rd.VERDICTS).exists():
            measurements = rd.load_measurements(run)
            evidence = build_evidence(groups, rows, measurements.byRow, qualified_verdicts(groups, screen))
            kind = WorthinessKind(mode, measurements.comparability, evidence, directory)
            try:
                records = active_outbox(directory).records()
            except OutboxError as e:
                out[directory.name] = [str(e)]
                continue
            saved = Verdicts.from_json(read_json(directory / rd.VERDICTS))
            out[directory.name] = kind.validate(saved, records)
    return out


def _dossiers(run: Path, groups: dict, screen: dict[int, Verdict] | None, catalog: Catalog) -> dict[str, list[str]]:
    out, handler = {}, catalog.handler()
    for directory in sorted((run / rd.APPS).glob(f"*/{rd.DOSSIERS}")):
        scopes = [Scope.from_json(s) for s in read_json(directory.parent / rd.SCOPES)["scopes"]]
        verdicts = handler.app_verdicts(groups, screen, read_json(directory.parent / rd.APP).get("targetSdk"))
        out[str(directory.relative_to(run))] = validate_dossiers(read_json(directory), scopes, groups, verdicts)
    return out


def _grouping(grouping: GroupingPaths) -> list[str]:
    try:
        records = active_outbox(grouping.root).records()
    except OutboxError as e:
        return [str(e)]
    if not grouping.knowledge.exists():
        return [f"{grouping.knowledge.name} missing for {len(records)} committed records"] if records else []
    try:
        saved = Knowledge.from_json(read_json(grouping.knowledge))
    except (KeyError, TypeError, ValueError) as e:
        return [f"{grouping.knowledge.name} does not parse: {e}"]
    return GroupingKind(grouping).validate(saved, records)


def _screen(grouping: GroupingPaths, catalog: Catalog) -> dict[str, list[str]]:
    if not grouping.screen.exists():
        return {}
    items, doc = read_items(read_json(grouping.items)), read_json(grouping.screen)
    problems = validate_screen_document(doc, items)
    return {"grouping/screen.json": problems or catalog.mismatch(rd.load_screen_catalog(grouping))}
