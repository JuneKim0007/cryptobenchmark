"""worthiness state: one verdict per group; static verdicts equal what triage computes; model
verdicts name members and improving pairs, and equal the replay of the journal."""
from __future__ import annotations

from ..dto import GroupEvidence, Verdicts
from ..orchestrate.decisions.worthiness import WorthinessKind
from ..result.modes import Mode
from ..result.triage import triage
from .replay import replay, validate_journal


def validate_verdicts(verdicts: Verdicts, evidence: list[GroupEvidence], mode: Mode,
                      entries: list[dict]) -> list[str]:
    by_id = {e.itemId: e for e in evidence}
    ask, decided = triage(evidence, mode)
    asked = {e.itemId: e for e in ask}
    problems = validate_journal(entries, asked)
    if verdicts.mode != mode.name:
        problems.append(f"verdicts are for mode {verdicts.mode}, not {mode.name}")
    problems += [f"{g}: no verdict" for g in by_id if g not in verdicts.verdicts]
    problems += [f"{g}: verdict for an unknown group" for g in verdicts.verdicts if g not in by_id]
    for v in decided:
        if verdicts.verdicts.get(v.groupId) != v:
            problems.append(f"{v.groupId}: static verdict differs from triage ({v.decision})")
    for g, v in verdicts.verdicts.items():
        if g in asked and v.source == "static":
            problems.append(f"{g}: needs a decision but holds a static verdict")
        if v.proxy != mode.proxy:
            problems.append(f"{g}: proxy flag {v.proxy} does not match mode {mode.name}")
        members = set(by_id[g].members) if g in by_id else set()
        problems += [f"{g}: pair {p.fromItem} -> {p.toItem} names a non-member"
                     for p in v.pairs if {p.fromItem, p.toItem} - members]
    kind = WorthinessKind(mode, [], prompt="")
    rebuilt = replay(kind, entries, asked, Verdicts(mode.name))
    model_made = {g: v for g, v in verdicts.verdicts.items() if v.source != "static"}
    if rebuilt.verdicts != model_made or rebuilt.version != verdicts.version:
        problems.append("model verdicts differ from the replay of the journal")
    return problems
