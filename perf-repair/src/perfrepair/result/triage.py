from __future__ import annotations

from ..dto import GroupEvidence, Verdict
from .modes import Mode


def triage(evidence: list[GroupEvidence], mode: Mode) -> tuple[list[GroupEvidence], list[Verdict]]:
    ask, decided = [], []
    for e in evidence:
        pairs = [(p, c) for c in e.configurations for p in c.pairs]
        improving = [(p, c) for p, c in pairs if mode.improves(p)]
        if not pairs:
            decided.append(Verdict(e.groupId, mode.name, "not_comparable",
                                   "no configuration measured two primitives of this group", "static", mode.proxy))
        elif not improving:
            decided.append(Verdict(e.groupId, mode.name, "no_improvement",
                                   f"no replacement improves under {mode.name}: {mode.rule}", "static", mode.proxy))
        elif all(p.ciOverlap for p, _ in improving):
            decided.append(Verdict(e.groupId, mode.name, "within_noise",
                                   "every improving pair's median 95% intervals overlap", "static", mode.proxy))
        else:
            ask.append(e)
    return ask, decided
