"""Grades a pImprove into the levels of criteria.yaml; a level is reported, never used to reject."""
from __future__ import annotations

from .modes import CRITERIA
from ..files import read_yaml

TOO_FEW_RUNS = "too_few_runs"
LEVELS: tuple[tuple[str, float], ...] = tuple(
    (lv["name"], float(lv["atLeast"])) for lv in sorted(read_yaml(CRITERIA)["levels"], key=lambda lv: -lv["atLeast"]))


def level(p_improve: float | None) -> str:
    if p_improve is None:
        return TOO_FEW_RUNS
    return next(name for name, floor in LEVELS if p_improve >= floor)


def describe(p_improve: float | None) -> str:
    return TOO_FEW_RUNS if p_improve is None else f"{p_improve:.0%} ({level(p_improve)})"
