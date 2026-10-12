"""Rebuilds a decision state from its journal alone; a saved state that differs was not produced by
the recorded decisions (edited by hand, or written by another run)."""
from __future__ import annotations

from collections import Counter

from ..orchestrate.decisions.kind import DecisionKind

FINAL = ("applied", "fallback")


def replay(kind: DecisionKind, entries: list[dict], items: dict, state):
    for e in entries:
        if e["status"] in FINAL:
            kind.apply(items[e["itemId"]], kind.decision_from_json(e["decision"]), state)
    return state


def validate_journal(entries: list[dict], items: dict) -> list[str]:
    """Steps contiguous from 0, known items, one final answer per item, attempts counted from 1."""
    problems = []
    if [e["step"] for e in entries] != list(range(len(entries))):
        problems.append("steps are not 0..n-1 in order")
    problems += [f"step {e['step']}: unknown item {e['itemId']}" for e in entries if e["itemId"] not in items]
    finals = Counter(e["itemId"] for e in entries if e["status"] in FINAL)
    problems += [f"{i}: {n} final answers" for i, n in finals.items() if n > 1]
    for e in entries:
        if e["status"] in FINAL and "decision" not in e:
            problems.append(f"step {e['step']}: {e['status']} without a decision")
        if e["status"] == "refused" and not e["problems"]:
            problems.append(f"step {e['step']}: refused without problems")
    return problems
