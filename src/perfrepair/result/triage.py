from __future__ import annotations

from ..dto import Configuration, GroupEvidence, PairMetrics, Verdict
from .modes import Mode

# Same threshold as cryptobenchmark's analyze.py "unstable(CoV>5%)".
MAX_CV = 0.05


def _stable(pair: PairMetrics, config: Configuration) -> bool:
    cv = {m.itemId: m.timeNs.cv for m in config.members if m.timeNs is not None}
    return all((cv.get(i) or 0) <= MAX_CV for i in (pair.fromItem, pair.toItem))


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
        elif not any(_stable(p, c) for p, c in improving):
            decided.append(Verdict(e.groupId, mode.name, "unstable",
                                   f"every improving pair has a member with CoV above {MAX_CV:.0%}", "static", mode.proxy))
        else:
            ask.append(e)
    return ask, decided
