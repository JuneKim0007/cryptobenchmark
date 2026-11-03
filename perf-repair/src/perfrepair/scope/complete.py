"""Completions onto a lifecycle and a scope: code-derived origins stay; a completion only fills an open requirement."""
from __future__ import annotations

from dataclasses import replace

from ..dto.gaps import UNKNOWN_CHOICE, USE_GAP, Answer, ScopeGaps
from ..dto.lifecycle import Completion, Lifecycle
from ..dto.site import Scope
from .facts import completed_key_source


def fill(lc: Lifecycle, completions: dict[tuple, Completion], use: Completion | None = None) -> Lifecycle:
    """A requirement already completed by code keeps that; only an open requirement takes a completion."""
    rows = tuple(replace(r, completed=completions[r.key]) if r.key in completions and r.open
                 and (r.completed is None or r.completed.by_model) else r for r in lc.requirements)
    return replace(lc, requirements=rows, use=use or lc.use)


def _completions(entry: ScopeGaps, answers: tuple[Answer, ...], source: str) -> dict[tuple, Completion]:
    offered = {g.id: g for g in entry.offered}
    out = {}
    for a in answers:
        gap = offered.get(a.gap)
        if gap is not None and a.choice != UNKNOWN_CHOICE:
            line = next(c for c in gap.candidates if c.id == a.choice)
            out[gap.requirement] = Completion(a.origin, line.line, line.file, source)
    return out


def apply_answers(scope: Scope, entry: ScopeGaps, answers: tuple[Answer, ...], source: str) -> Scope:
    """An `unknown` answer leaves the requirement as code read it; its record stays in completed.json."""
    found = _completions(entry, answers, source)
    use = next((c for key, c in found.items() if key[0] == USE_GAP), None)
    lc = fill(scope.lifecycle, found, use)
    return replace(scope, lifecycle=lc, keySource=completed_key_source(lc, scope.keySource))
