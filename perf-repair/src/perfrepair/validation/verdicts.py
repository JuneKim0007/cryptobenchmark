from __future__ import annotations

from ..dto import GroupEvidence, Verdicts
from ..result.modes import Mode
from ..result.triage import triage


def validate_verdicts(verdicts: Verdicts, evidence: list[GroupEvidence], mode: Mode) -> list[str]:
    by_id = {e.groupId: e for e in evidence}
    ask, decided = triage(evidence, mode)
    asked = {e.groupId for e in ask}
    problems = [] if verdicts.mode == mode.name else [f"verdicts are for mode {verdicts.mode}, not {mode.name}"]
    problems += [f"{g}: verdict for an unknown group" for g in verdicts.verdicts if g not in by_id]
    problems += [f"{v.groupId}: static verdict differs from triage ({v.decision})"
                 for v in decided if verdicts.verdicts.get(v.groupId) != v]
    for g, v in verdicts.verdicts.items():
        if g in asked and v.source == "static":
            problems.append(f"{g}: needs a decision but holds a static verdict")
        if v.proxy != mode.proxy:
            problems.append(f"{g}: proxy flag {v.proxy} does not match mode {mode.name}")
        members = set(by_id[g].members) if g in by_id else set()
        problems += [f"{g}: pair {p.fromItem} -> {p.toItem} names a non-member"
                     for p in v.pairs if {p.fromItem, p.toItem} - members]
    return problems
