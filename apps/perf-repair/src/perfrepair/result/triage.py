from __future__ import annotations

from ..dto import GroupEvidence, Verdict
from ..dto.perf_mode import no_evidence
from .modes import Mode


def _missing(e: GroupEvidence, mode: Mode) -> list[str]:
    return sorted({m for c in e.configurations for p in c.pairs for m in mode.missing(p)})


def triage(evidence: list[GroupEvidence], mode: Mode) -> tuple[list[GroupEvidence], list[Verdict]]:
    """Static verdicts from the numbers alone; confidence never settles a group, it rides along to the model."""
    ask, decided = [], []
    for e in evidence:
        judged = {mode.judge(p) for c in e.configurations for p in c.pairs}
        if not judged:
            decided.append(Verdict(e.groupId, mode.name, "not_comparable",
                                   "no configuration measured two primitives of this group", "static"))
        elif "improves" in judged:
            ask.append(e)
        elif "not_measured" in judged:
            decided.append(Verdict(e.groupId, mode.name, "not_measured",
                                   f"{no_evidence(_missing(e, mode) or mode.perf.names)}; a pair has no data for it under {mode.name}",
                                   "static"))
        else:
            decided.append(Verdict(e.groupId, mode.name, "no_improvement",
                                   f"no replacement improves under {mode.name}: {mode.rule}", "static"))
    return ask, decided
