"""compare(): the one before/after comparison the report, the evidence and the dossier estimates use; pImprove, the
probability that the candidate's median is better, by the process- and block-aware bootstrap."""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from ..data_handler.inbound.bootstrap import RESAMPLES, SEED, resample, runs_of
from ..dto import Summary
from ..dto.dossier import ENERGY_KINDS_DIFFER, ZERO_MEDIAN

Processes = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class Comparison:
    """ratio: None with a reason `<code>: <detail>`; comparable: False when no number of the pair means anything."""
    ratio: float | None
    pImprove: float | None
    n: int
    reason: str | None = None
    comparable: bool = True


def p_improve(before: Processes, after: Processes, resamples: int = RESAMPLES, seed: int = SEED) -> float | None:
    if runs_of(before) < 2 or runs_of(after) < 2:
        return None
    rng, wins = random.Random(seed), 0.0
    for _ in range(resamples):
        b, a = statistics.median(resample(rng, before)), statistics.median(resample(rng, after))
        wins += 1.0 if a < b else 0.5 if a == b else 0.0
    return wins / resamples


def compare(before: Summary, after: Summary, lower_is_better: bool = True) -> Comparison:
    """`after` against `before`, oriented so a ratio below 1 and a high pImprove are better: after ÷ before of the
    pooled medians, inverted for a metric where higher is better. A measured side and an estimated one are not
    comparable; a zero median (no allocations) has no ratio, while pImprove still compares the runs."""
    if before.kind != after.kind:
        return Comparison(None, None, 0, f"{ENERGY_KINDS_DIFFER}: {before.kind} before, {after.kind} after", False)
    base, other = (before, after) if lower_is_better else (after, before)
    p, n = p_improve(base.processes, other.processes), min(before.n, after.n)
    if not base.median:
        return Comparison(None, p, n, f"{ZERO_MEDIAN}: the {'before' if lower_is_better else 'after'} median is 0")
    return Comparison(other.median / base.median, p, n)
