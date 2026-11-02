from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto import Verdicts
from ..dto.grouping_state import Knowledge
from ..dto.site import Scope
from ..files import read_json
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..grouping.paths import GroupingPaths
from ..grouping.report.checks import read_groups
from ..ai.evaluate.worthiness.kind import WorthinessKind
from ..ai.runtime.engine.outbox import OutboxError, active_outbox
from ..result.evidence import build_evidence
from ..result.modes import MODES
from .dossiers import validate_dossiers
from .app import validate_app_dir
from .failure import ValidationFailed
from .grouping.interop import validate_interop
from .measurements import validate_measurements
from .report import validate_report, validate_summary
from .rows import validate_rows
from .run_log import validate_run_log


def validate_run(run: Path) -> dict[str, list[str]]:
    run, out = Path(run), {}
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
    if grouping.items.exists():
        out["grouping"] = _grouping(grouping)
    if not grouping.groups.exists():
        return out
    try:
        groups = read_groups(grouping)
        out["grouping/groups.json"] = []
    except ValidationFailed as e:
        out["grouping/groups.json"] = e.problems
        return out
    out |= validate_interop(groups, grouping.interop_plan, grouping.interop)
    for directory in sorted((run / rd.APPS).glob(f"*/{rd.DOSSIERS}")):
        scopes = [Scope.from_json(s) for s in read_json(directory.parent / rd.SCOPES)["scopes"]]
        out[str(directory.relative_to(run))] = validate_dossiers(read_json(directory), scopes, groups)
    for mode in MODES.values():
        directory = rd.worthiness(run, mode.name)
        if (directory / rd.VERDICTS).exists():
            measurements = rd.load_measurements(run)
            kind = WorthinessKind(mode, measurements.comparability, build_evidence(groups, rows, measurements.byRow),
                                  directory)
            try:
                records = active_outbox(directory).records()
            except OutboxError as e:
                out[directory.name] = [str(e)]
                continue
            saved = Verdicts.from_json(read_json(directory / rd.VERDICTS))
            out[directory.name] = kind.validate(saved, records)
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
