"""Bootstrap of a median that keeps the run structure: whole processes, then circular blocks of runs inside each."""
from __future__ import annotations

import math
import random
import statistics

RESAMPLES = 2000
SEED = 1
LEVEL = 0.95


def block_length(n: int) -> int:
    # sqrt(n) rather than the textbook n^(1/3): runs drift with heat, so longer blocks keep more of it
    return max(1, math.ceil(math.sqrt(n)))


def _blocks(rng: random.Random, runs: tuple[float, ...]) -> list[float]:
    n, size, out = len(runs), block_length(len(runs)), []
    while len(out) < n:
        start = rng.randrange(n)
        out.extend(runs[(start + i) % n] for i in range(size))
    return out[:n]


def resample(rng: random.Random, processes: tuple[tuple[float, ...], ...]) -> list[float]:
    chosen = [processes[rng.randrange(len(processes))] for _ in processes] if len(processes) > 1 else processes
    return [v for p in chosen for v in _blocks(rng, p)]


def runs_of(processes: tuple[tuple[float, ...], ...]) -> int:
    return sum(len(p) for p in processes)


def median_interval(processes: tuple[tuple[float, ...], ...]) -> tuple[float | None, float | None]:
    """Percentile interval of the median; None when fewer than two runs leave nothing to resample."""
    if runs_of(processes) < 2:
        return None, None
    rng = random.Random(SEED)
    medians = sorted(statistics.median(resample(rng, processes)) for _ in range(RESAMPLES))
    tail = (1 - LEVEL) / 2
    return medians[int(tail * RESAMPLES)], medians[math.ceil((1 - tail) * RESAMPLES) - 1]
