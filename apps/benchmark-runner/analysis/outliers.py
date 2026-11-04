"""Outlier filter: keep every run when none is an outlier, else drop the farthest from the mean one at a time."""
import statistics

Z = 3.0  # TEMP (issue): an outlier lies more than Z sample standard deviations from the others' mean
MAX_REMOVED = 20


def _beyond(value, others):
    if len(others) < 2:
        return False
    spread = statistics.stdev(others)
    return spread > 0 and abs(value - statistics.fmean(others)) / spread > Z


def split(runs):
    """Returns (kept, removed); more than MAX_REMOVED removals falls back to keeping every run."""
    runs = list(runs)
    if not any(_beyond(value, runs[:i] + runs[i + 1:]) for i, value in enumerate(runs)):
        return runs, []
    kept, removed = list(runs), []
    while len(kept) > 2:
        mean = statistics.fmean(kept)
        farthest = max(range(len(kept)), key=lambda i: abs(kept[i] - mean))
        rest = kept[:farthest] + kept[farthest + 1:]
        if not _beyond(kept[farthest], rest):
            break
        removed.append(kept[farthest])
        kept = rest
        if len(removed) > MAX_REMOVED:
            return runs, []
    return kept, removed
