"""Validates every artifact present in a run directory, each against the ones it depends on."""
from __future__ import annotations

from pathlib import Path

from .. import run_dir as rd
from ..orchestrate import journal
from ..dto.grouping import read_items
from ..files import read_json
from ..grouping.paths import GroupingPaths
from ..result.evidence import build_evidence
from ..result.modes import MODES
from .measurements import validate_measurements
from .grouping.output import validate_output
from .rows import validate_rows
from .run_log import validate_run_log
from .verdicts import validate_verdicts


def validate_run(run: Path) -> dict[str, list[str]]:
    run, out = Path(run), {}
    rows = rd.load_rows(run)
    out[rd.ROWS] = validate_rows(rows)
    if (run / rd.MEASUREMENTS).exists():
        out[rd.MEASUREMENTS] = validate_measurements(rd.load_measurements(run), rows)
    if (run / rd.RUN_LOG).exists():
        out[rd.RUN_LOG] = validate_run_log(rd.load_run_log(run), rows)
    grouping = GroupingPaths(run)
    if not grouping.groups.exists():
        return out
    groups = read_json(grouping.groups)
    out["grouping/groups.json"] = validate_output(groups, {i.id: i for i in read_items(read_json(grouping.items))})
    for mode in MODES.values():
        kind = rd.worthiness(mode.name)
        if rd.state(run, kind).exists():
            evidence = build_evidence(groups, rows, rd.load_measurements(run).byRow)
            out[kind] = validate_verdicts(rd.load_verdicts(run, mode.name), evidence, mode,
                                          journal.read(rd.journal(run, kind)))
    return out
