"""The run count's calculations: no I/O, no settings, no logging."""
from __future__ import annotations

import math
import random
import statistics

Z_95 = 1.96
SUBSAMPLE_SIZES = (5, 8, 10, 12, 15, 20, 25, 30, 35, 40, 50)
SUBSAMPLE_DRAWS = 800


def rank_interval(values: list[float], z: float = Z_95) -> tuple[float, float, float]:
    """Low, median and high of the distribution-free interval of the median, from ranks (n - z*sqrt(n))/2 and 1 + (n + z*sqrt(n))/2."""
    ordered, n = sorted(values), len(values)
    low = max(math.floor((n - z * math.sqrt(n)) / 2), 1)
    high = min(math.ceil(1 + (n + z * math.sqrt(n)) / 2), n)
    return ordered[low - 1], statistics.median(ordered), ordered[high - 1]


def half_width(values: list[float], z: float = Z_95) -> float:
    """The interval's larger side as a fraction of the median."""
    low, middle, high = rank_interval(values, z)
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
