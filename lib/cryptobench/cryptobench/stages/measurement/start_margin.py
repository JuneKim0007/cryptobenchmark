"""The temperature gate's start margin: no I/O, no settings, no logging; dynamic_temperature is its facade."""
from __future__ import annotations

from dataclasses import dataclass, replace

HOT, CLEAN, IGNORED = "hot", "clean", "ignored"
ROUNDING = 6


@dataclass(frozen=True)
class StartMarginRule:
    """How far under the kept temperature a run may start, in Celsius, and how that distance moves."""
    initial: float
    factor: float
    maximum: float
    clean_runs: int
    recovery: float


@dataclass(frozen=True)
class StartMargin:
    celsius: float
    clean_streak: int = 0


def first_margin(rule: StartMarginRule) -> StartMargin:
    return StartMargin(rule.initial)


def start_limit(kept_celsius: float, margin: StartMargin) -> float:
    """The hottest skin temperature a run may start at."""
    return round(kept_celsius - margin.celsius, ROUNDING)


def next_margin(margin: StartMargin, outcome: str, rule: StartMarginRule) -> StartMargin:
    """A hot run widens the margin sharply; enough clean runs in a row narrow it a little, never below the initial; anything else leaves it."""
    if outcome == HOT:
        return StartMargin(round(min(margin.celsius * rule.factor, rule.maximum), ROUNDING))
    if outcome != CLEAN:
        return margin
    if margin.clean_streak + 1 < rule.clean_runs:
        return replace(margin, clean_streak=margin.clean_streak + 1)
    return StartMargin(round(max(margin.celsius - rule.recovery, rule.initial), ROUNDING))
