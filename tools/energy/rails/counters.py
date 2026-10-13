"""Rail counters are cumulative microjoules; a window edge between polls is interpolated linearly."""
from bisect import bisect_left


def at(samples, ts):
    times = [t for t, _ in samples]
    if not samples or ts < times[0] or ts > times[-1]:
        raise ValueError(f"uncovered: {ts} outside the rail samples [{times[0] if times else '-'}, {times[-1] if times else '-'}]")
    i = bisect_left(times, ts)
    if times[i] == ts:
        return samples[i][1]
    (t0, v0), (t1, v1) = samples[i - 1], samples[i]
    return v0 + (v1 - v0) * (ts - t0) / (t1 - t0)


def between(samples, start, end):
    if end < start:
        raise ValueError(f"empty_window: end {end} before start {start}")
    return at(samples, end) - at(samples, start)


def polls_inside(samples, start, end):
    return sum(1 for t, _ in samples if start <= t <= end)


def whole(samples):
    return samples[-1][1] - samples[0][1] if len(samples) > 1 else 0.0
