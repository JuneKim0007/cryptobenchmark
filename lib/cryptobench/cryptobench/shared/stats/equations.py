"""The run count's calculations: no I/O, no settings, no logging."""
from __future__ import annotations

import math
import random
import statistics

LEVEL_95 = 0.95
SUBSAMPLE_SIZES = (5, 8, 10, 12, 15, 20, 25, 30, 35, 40, 50)
SUBSAMPLE_DRAWS = 800


def median_ranks(n: int, level: float = LEVEL_95) -> tuple[int, int, float]:
    """1-based ranks of the distribution-free interval of the median, from Binomial(n, 1/2), and its exact coverage."""
    tail = lambda rank: sum(math.comb(n, k) for k in range(rank)) / 2 ** n
    low = 1
    while 2 * (low + 1) <= n + 1 and tail(low + 1) <= (1 - level) / 2:
        low += 1
    return low, n + 1 - low, 1 - 2 * tail(low)


def rank_interval(values: list[float], level: float = LEVEL_95) -> tuple[float, float, float]:
    """Low, median and high of the distribution-free interval of the median."""
    ordered = sorted(values)
    low, high, _ = median_ranks(len(ordered), level)
    return ordered[low - 1], statistics.median(ordered), ordered[high - 1]


def half_width(values: list[float], level: float = LEVEL_95) -> float:
    """The interval's larger side as a fraction of the median."""
    low, middle, high = rank_interval(values, level)
    return max(middle - low, high - middle) / middle


def runs_needed(values: list[float], target: float, seed: int = 0) -> int | None:
    """The smallest listed run count whose typical interval is within target of the median; None when the values cannot show one."""
    draw = random.Random(seed)
    for size in SUBSAMPLE_SIZES:
        if size > len(values):
            return None
        if statistics.median(half_width(draw.sample(values, size)) for _ in range(SUBSAMPLE_DRAWS)) <= target:
            return size
    return None
