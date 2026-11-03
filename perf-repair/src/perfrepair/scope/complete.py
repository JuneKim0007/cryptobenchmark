"""Completions onto a lifecycle and a scope: code-derived origins stay; a completion only fills an open requirement."""
from __future__ import annotations

from dataclasses import replace

from ..dto.lifecycle import Completion, Lifecycle


def fill(lc: Lifecycle, completions: dict[tuple, Completion], use: Completion | None = None) -> Lifecycle:
    """A requirement already completed by code keeps that; only an open requirement takes a completion."""
    rows = tuple(replace(r, completed=completions[r.key]) if r.key in completions and r.open
                 and (r.completed is None or r.completed.by_model) else r for r in lc.requirements)
    return replace(lc, requirements=rows, use=use or lc.use)


