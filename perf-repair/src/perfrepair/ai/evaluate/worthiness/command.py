from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .... import run_dir as rd
from ....dto import Verdicts
from ....dto.screen import qualified_verdicts
from ....files import write_json
from ....run_dir import GroupingPaths
from ....validation.grouping.output import read_groups
from ....result.evidence import build_evidence
from ....result.modes import Mode
from ....validation import require, validate_measurements
from ...runtime.agent import Conversations, ScriptedConversations
from .kind import WorthinessKind, charter
from ...runtime.engine.ask import Limits
from ...runtime.engine.decide import decide
from ...runtime.engine.events import Where
from ...runtime.prompt import PromptLibrary

DRY_RUN = ScriptedConversations(lambda *_: {"decision": "skip", "pairs": [], "reason": "dry run: no model was called"})
EVIDENCE_SCHEMA_VERSION = 1


def worthiness(run_path: Path, mode: Mode, conversations: Conversations, library: PromptLibrary, limits: Limits = Limits(),
               limit: int | None = None, echo=print) -> Verdicts:
    rows, measurements = rd.load_rows(run_path), rd.load_measurements(run_path)
    require(rd.MEASUREMENTS, validate_measurements(measurements, rows))
    grouping = GroupingPaths(run_path)
    groups = read_groups(grouping)
    evidence = build_evidence(groups, rows, measurements.byRow, qualified_verdicts(groups, rd.load_screen(grouping)))
    directory = rd.worthiness(run_path, mode.name)
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / rd.EVIDENCE, {"schemaVersion": EVIDENCE_SCHEMA_VERSION, "groups": [asdict(e) for e in evidence]})
    kind = WorthinessKind(mode, measurements.comparability, evidence, directory)
    verdicts = decide(kind, charter(library), conversations, directory, limits, limit, echo,
                      Where("worthiness", mode.name))
    counts: dict[str, int] = {}
    for v in verdicts.verdicts.values():
        counts[v.decision] = counts.get(v.decision, 0) + 1
    echo(f"{mode.name}{' (proxy)' if mode.proxy else ''}: {len(evidence)} groups, {len(kind.items())} asked, {counts}")
    return verdicts
