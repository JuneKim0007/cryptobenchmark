"""Tests and intervals over a list of values, one per process or one process's own samples: normality, rank tests, effect size,
a bootstrap of a ratio of medians and drift between thirds."""
from __future__ import annotations

import math
import random
import statistics
from functools import lru_cache

NORMAL = statistics.NormalDist()
ALPHA = 0.05
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261120
QQ_MIN = 8
QQ_CRITICAL_DRAWS = 20_000
QQ_CRITICAL_SEED = 1975
EXACT_MAX = 25          # Mann-Whitney is exact when both sides are at most this size and nothing ties
DRIFT_MIN_TEST = 8      # thirds smaller than this get a ratio but no p
EXACT, NORMAL_APPROX = "exact", "normal"
# Romano et al. (2006) thresholds on |Cliff's delta|
CLIFF_LABELS = ((0.147, "negligible"), (0.33, "small"), (0.474, "medium"), (math.inf, "large"))


def _poly(coefficients, x):
    return sum(c * x ** i for i, c in enumerate(coefficients))


def normal_scores(n: int) -> list[float]:
    """Blom's expected normal order statistics, the x axis of a normal probability plot."""
    return [NORMAL.inv_cdf((i - 0.375) / (n + 0.25)) for i in range(1, n + 1)]


def qq_score(values: list[float]) -> float | None:
    """Probability-plot r: the correlation of the sorted values with their normal scores, 1 a straight Q-Q line; None below 3 values or with no spread."""
    if len(values) < 3 or max(values) == min(values):
        return None
    return max(0.0, statistics.correlation(sorted(values), normal_scores(len(values))))


@lru_cache(maxsize=None)
def qq_critical(n: int, alpha: float = ALPHA, draws: int = QQ_CRITICAL_DRAWS, seed: int = QQ_CRITICAL_SEED) -> float:
    """The alpha quantile of qq_score over seeded normal samples of size n, Filliben-style PPCC table built on Blom scores."""
    rng, scores = random.Random(seed * 100_003 + n), normal_scores(n)
    rs = sorted(statistics.correlation(sorted(rng.gauss(0, 1) for _ in range(n)), scores) for _ in range(draws))
    return rs[int(alpha * draws)]


def qq_test(values: list[float]) -> tuple[float, float, bool] | None:
    """(r, its critical value at ALPHA, whether r reaches it); None below QQ_MIN values, where the score is not meaningful."""
    r = qq_score(values)
    if len(values) < QQ_MIN or r is None:
        return None
    critical = qq_critical(len(values))
    return r, critical, r >= critical


def shapiro_wilk(values: list[float]) -> tuple[float, float] | None:
    """W and its p-value by Royston's AS R94 (3 <= n <= 5000); None outside that range or with no spread."""
    x, n = sorted(values), len(values)
    if not 3 <= n <= 5000 or x[0] == x[-1]:
        return None
    if n == 3:
        a = [-math.sqrt(0.5), 0.0, math.sqrt(0.5)]
    else:
        m = normal_scores(n)
        mm, u = sum(v * v for v in m), 1 / math.sqrt(n)
        an = m[-1] / math.sqrt(mm) + _poly((0, 0.221157, -0.147981, -2.071190, 4.434685, -2.706056), u)
        if n > 5:
            an1 = m[-2] / math.sqrt(mm) + _poly((0, 0.042981, -0.293762, -1.752461, 5.682633, -3.582633), u)
            phi = (mm - 2 * m[-1] ** 2 - 2 * m[-2] ** 2) / (1 - 2 * an ** 2 - 2 * an1 ** 2)
            a = [v / math.sqrt(phi) for v in m]
            a[0], a[1], a[-2], a[-1] = -an, -an1, an1, an
        else:
            phi = (mm - 2 * m[-1] ** 2) / (1 - 2 * an ** 2)
            a = [v / math.sqrt(phi) for v in m]
            a[0], a[-1] = -an, an
    mean = statistics.fmean(x)
    w = min(sum(ai * xi for ai, xi in zip(a, x)) ** 2 / sum((xi - mean) ** 2 for xi in x), 1.0)
    if n == 3:
        return w, max(0.0, min(1.0, 6 / math.pi * (math.asin(math.sqrt(w)) - math.asin(math.sqrt(0.75)))))
    if w >= 1.0:
        return w, 1.0
    y = math.log(1 - w)
    if n <= 11:
        gamma = _poly((-2.273, 0.459), n)
        if y >= gamma:
            return w, 0.0
        y = -math.log(gamma - y)
        mu, sigma = _poly((0.5440, -0.39978, 0.025054, -6.714e-4), n), math.exp(_poly((1.3822, -0.77857, 0.062767, -0.0020322), n))
    else:
        ln = math.log(n)
        mu, sigma = _poly((-1.5861, -0.31082, -0.083751, 0.0038915), ln), math.exp(_poly((-0.4803, -0.082676, 0.0030302), ln))
    return w, 1 - NORMAL.cdf((y - mu) / sigma)


def _ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks, i = [0.0] * len(values), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in range(i, j + 1):
            ranks[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


@lru_cache(maxsize=None)
def _u_counts(m: int, n: int) -> tuple[int, ...]:
    """How many orderings of m and n distinct values give each U, U counting pairs where the m side is larger."""
    if not m or not n:
        return (1,)
    top_m, top_n = _u_counts(m - 1, n), _u_counts(m, n - 1)
    return tuple((top_m[u - n] if 0 <= u - n < len(top_m) else 0) + (top_n[u] if u < len(top_n) else 0) for u in range(m * n + 1))


def mann_whitney(a: list[float], b: list[float]) -> tuple[float, float, str] | None:
    """U of a, the two-sided p and how it was found: exact without ties when both sides are at most EXACT_MAX, otherwise the
    normal approximation with tie and continuity corrections; None when a side is empty or all values tie."""
    n1, n2 = len(a), len(b)
    if not n1 or not n2:
        return None
    pooled = list(a) + list(b)
    ranks = _ranks(pooled)
    u = sum(ranks[:n1]) - n1 * (n1 + 1) / 2
    n = n1 + n2
    tie_sizes = _tie_sizes(pooled)
    if not tie_sizes and max(n1, n2) <= EXACT_MAX:
        counts, k = _u_counts(n1, n2), round(u)
        tail = min(sum(counts[:k + 1]), sum(counts[k:]))
        return u, min(1.0, 2 * tail / math.comb(n, n1)), EXACT
    ties = sum(t ** 3 - t for t in tie_sizes)
    variance = n1 * n2 / 12 * ((n + 1) - ties / (n * (n - 1)))
    if variance <= 0:
        return None
    z = max(abs(u - n1 * n2 / 2) - 0.5, 0.0) / math.sqrt(variance)
    return u, min(1.0, 2 * (1 - NORMAL.cdf(z))), NORMAL_APPROX


def _tie_sizes(values):
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    return [c for c in counts.values() if c > 1]


def cliffs_delta(a: list[float], b: list[float]) -> tuple[float, str]:
    """P(b > a) - P(b < a) over every pair, and its Romano magnitude."""
    greater = sum((y > x) - (y < x) for x in a for y in b)
    delta = greater / (len(a) * len(b))
    return delta, next(label for limit, label in CLIFF_LABELS if abs(delta) < limit)


def ratio_of_medians(base: list[float], other: list[float], resamples: int = BOOTSTRAP_RESAMPLES,
                     seed: int = BOOTSTRAP_SEED, level: float = 0.95) -> tuple[float, float, float] | None:
    """median(other) / median(base) and its percentile bootstrap interval, each side's values resampled on their own; None at a zero median."""
    if not base or not other or statistics.median(base) == 0:
        return None
    rng = random.Random(seed)
    draws = []
    for _ in range(resamples):
        low = statistics.median(rng.choices(base, k=len(base)))
        if low:
            draws.append(statistics.median(rng.choices(other, k=len(other))) / low)
    draws.sort()
    tail = (1 - level) / 2
    return (statistics.median(other) / statistics.median(base), draws[int(tail * len(draws))],
            draws[math.ceil((1 - tail) * len(draws)) - 1])


def drift(samples: list[float]) -> tuple[float, float | None, str | None] | None:
    """median(last third) / median(first third) of one process's samples in order, and the Mann-Whitney p between the thirds
    and its method, both None for thirds under DRIFT_MIN_TEST."""
    third = len(samples) // 3
    if third < 2:
        return None
    first, last = samples[:third], samples[-third:]
    if not statistics.median(first):
        return None
    ratio = statistics.median(last) / statistics.median(first)
    test = mann_whitney(first, last) if third >= DRIFT_MIN_TEST else None
    return ratio, test and test[1], test and test[2]
