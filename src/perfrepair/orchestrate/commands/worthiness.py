"""Stage: grouping/groups.json + measurements → evidence-<mode>.json and worthiness-<mode>.state.json.

Static triage settles every group it can; only groups with an improving pair reach the model.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from ... import run_dir as rd
from ...dto import Verdicts
from ...files import write_json
from ...result.evidence import build_evidence
from ...result.modes import Mode
from ...result.triage import triage
from ...dto.grouping import read_items
from ...files import read_json
from ...grouping.paths import GroupingPaths
from ...validation import require, validate_measurements, validate_verdicts
from ...validation.grouping.output import validate_output
from .. import journal
from ..agent import Agent, FixedAgent
from ..decisions.worthiness import WorthinessKind, open_verdicts
from ..runner import RunPaths, run

DRY_RUN = FixedAgent({"decision": "skip", "pairs": [], "reason": "dry run: no model was called"})


def _evidence_json(evidence) -> dict:
    return {"schemaVersion": 1, "groups": [asdict(e) for e in evidence]}


def worthiness(run_path: Path, mode: Mode, agent: Agent, attempts: int = 2, echo=print) -> Verdicts:
    rows, measurements = rd.load_rows(run_path), rd.load_measurements(run_path)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    grouping = GroupingPaths(run_path)
    groups = read_json(grouping.groups)
    require("groups.json", validate_output(groups, {i.id: i for i in read_items(read_json(grouping.items))}))

    evidence = build_evidence(groups, rows, measurements.byRow)
    write_json(Path(run_path) / rd.EVIDENCE.format(mode=mode.name), _evidence_json(evidence))
    ask, decided = triage(evidence, mode)
    kind_name = rd.worthiness(mode.name)
    paths = RunPaths.under(run_path, kind_name)
    verdicts = open_verdicts(paths.state, mode)
    for v in decided:
        verdicts.verdicts.setdefault(v.groupId, v)
    kind = WorthinessKind(mode, measurements.comparability, name=kind_name)
    verdicts = run(kind, ask, agent, verdicts, paths, attempts, echo)
    write_json(paths.state, verdicts.to_json())
    require(kind_name, validate_verdicts(verdicts, evidence, mode, journal.read(paths.journal)))
    counts: dict[str, int] = {}
    for v in verdicts.verdicts.values():
        counts[v.decision] = counts.get(v.decision, 0) + 1
    echo(f"{mode.name}{' (proxy)' if mode.proxy else ''}: {len(evidence)} groups, {len(ask)} asked, {counts}")
    return verdicts
