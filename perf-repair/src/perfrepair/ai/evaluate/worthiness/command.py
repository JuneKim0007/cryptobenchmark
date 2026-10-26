from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .... import run_dir as rd
from ....dto import Verdicts
from ....files import write_json
from ....grouping.paths import GroupingPaths
from ....grouping.report.checks import read_groups
from ....result.evidence import build_evidence
from ....result.modes import Mode
from ....validation import require, validate_measurements
from ...runtime.agent import Conversations, ScriptedConversations
from .kind import WorthinessKind, charter
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.prompt import PromptLibrary

DRY_RUN = ScriptedConversations(lambda *_: {"decision": "skip", "pairs": [], "reason": "dry run: no model was called"})
EVIDENCE_SCHEMA_VERSION = 1


def worthiness(run_path: Path, mode: Mode, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
               limit: int | None = None, echo=print) -> Verdicts:
    rows, measurements = rd.load_rows(run_path), rd.load_measurements(run_path)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    evidence = build_evidence(read_groups(GroupingPaths(run_path)), rows, measurements.byRow)
    directory = rd.worthiness(run_path, mode.name)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / rd.EVIDENCE, {"schemaVersion": EVIDENCE_SCHEMA_VERSION, "groups": [asdict(e) for e in evidence]})
    kind = WorthinessKind(mode, measurements.comparability, evidence, directory)
    verdicts = decide(kind, charter(library), conversations, directory, limits, limit, echo)
    counts: dict[str, int] = {}
    for v in verdicts.verdicts.values():
        counts[v.decision] = counts.get(v.decision, 0) + 1
    echo(f"{mode.name}{' (proxy)' if mode.proxy else ''}: {len(evidence)} groups, {len(kind.items())} asked, {counts}")
    return verdicts
