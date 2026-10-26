from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..dto import Verdicts
from ..dto.grouping_state import Knowledge
from ..files import read_json
from ..ai.parse.grouping_assign.kind import GroupingKind
from ..grouping.paths import GroupingPaths
from ..grouping.report.checks import read_groups
from ..ai.evaluate.worthiness.kind import VERDICTS, WorthinessKind
from ..ai.runtime.engine.outbox import OutboxError, active_outbox
from ..result.evidence import build_evidence
from ..result.modes import MODES
from .failure import ValidationFailed
from .measurements import validate_measurements
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
    for mode in MODES.values():
        directory = rd.worthiness(run, mode.name)
        if (directory / VERDICTS).exists():
            measurements = rd.load_measurements(run)
            kind = WorthinessKind(mode, measurements.comparability, build_evidence(groups, rows, measurements.byRow),
                                  directory)
            try:
                records = active_outbox(directory).records()
            except OutboxError as e:
                out[directory.name] = [str(e)]
                continue
            saved = Verdicts.from_json(read_json(directory / VERDICTS))
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
