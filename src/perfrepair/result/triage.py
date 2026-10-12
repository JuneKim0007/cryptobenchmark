"""Decides statically every group that needs no judgement, so only real questions reach the model.

- no configuration with two measured primitives → `not_comparable`
- comparable, but no pair improves under the mode in any configuration → `no_improvement`
- otherwise → asked: the model decides whether an improvement is worth testing
"""
from __future__ import annotations

from ..dto import GroupEvidence, Verdict
from .modes import Mode


def triage(evidence: list[GroupEvidence], mode: Mode) -> tuple[list[GroupEvidence], list[Verdict]]:
    ask, decided = [], []
    for e in evidence:
        pairs = [p for c in e.configurations for p in c.pairs]
        if not pairs:
            decided.append(Verdict(e.groupId, mode.name, "not_comparable",
                                   "no configuration measured two primitives of this group", "static", mode.proxy))
        elif not any(mode.improves(p) for p in pairs):
            decided.append(Verdict(e.groupId, mode.name, "no_improvement",
                                   f"no replacement improves under {mode.name}: {mode.rule}", "static", mode.proxy))
        else:
            ask.append(e)
    return ask, decided
