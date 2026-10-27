"""pImprove: the probability that the candidate's median is lower, by the process- and block-aware bootstrap."""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from ..data_handler.inbound.bootstrap import RESAMPLES, SEED, resample, runs_of
from ..dto import Summary
from .confidence import TOO_FEW_RUNS

Processes = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Comparison:
    ratio: float
    pImprove: float | None
    n: int
    reason: str | None = None


def p_improve(before: Processes, after: Processes, resamples: int = RESAMPLES, seed: int = SEED) -> float | None:
    if runs_of(before) < 2 or runs_of(after) < 2:
        return None
    rng, wins = random.Random(seed), 0.0
    for _ in range(resamples):
        b, a = statistics.median(resample(rng, before)), statistics.median(resample(rng, after))
        wins += 1.0 if a < b else 0.5 if a == b else 0.0
    return wins / resamples


def compare(before: Summary, after: Summary) -> Comparison:
    """`after` against `before`; ratio is after ÷ before of the pooled medians, so below 1 is better."""
    n = min(before.n, after.n)
    p = p_improve(before.processes, after.processes)
    return Comparison(after.median / before.median, p, n, TOO_FEW_RUNS if p is None else None)
