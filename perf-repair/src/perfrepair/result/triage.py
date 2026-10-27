from __future__ import annotations

from ..dto import GroupEvidence, Verdict
from .modes import Mode


def triage(evidence: list[GroupEvidence], mode: Mode) -> tuple[list[GroupEvidence], list[Verdict]]:
    """Static verdicts from the numbers alone; confidence never settles a group, it rides along to the model."""
    ask, decided = [], []
    for e in evidence:
        judged = {mode.judge(p) for c in e.configurations for p in c.pairs}
        if not judged:
            decided.append(Verdict(e.groupId, mode.name, "not_comparable",
                                   "no configuration measured two primitives of this group", "static", mode.proxy))
        elif "improves" in judged:
            ask.append(e)
        elif "not_measured" in judged:
            decided.append(Verdict(e.groupId, mode.name, "not_measured",
                                   f"a pair is faster but lacks the allocation counts {mode.name} needs: {mode.rule}",
                                   "static", mode.proxy))
        else:
            decided.append(Verdict(e.groupId, mode.name, "no_improvement",
                                   f"no replacement improves under {mode.name}: {mode.rule}", "static", mode.proxy))
    return ask, decided
