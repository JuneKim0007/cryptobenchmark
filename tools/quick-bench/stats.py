"""Summary statistics for one case's per-run values: one definition each, shared by every table and chart."""
import math
import statistics


def quantile(values, percent):
    """Linear interpolation between ranks, as androidx.benchmark's getPercentile does."""
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percent / 100
    low = int(math.floor(rank))
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (rank - low)


def summarize(runs):
    n = len(runs)
    mean = statistics.fmean(runs)
    sd = statistics.stdev(runs) if n > 1 else 0.0          # sample sd (n - 1), as Jetpack
    q1, q3 = quantile(runs, 25), quantile(runs, 75)
    return {
        "n": n,
        "mean": mean,
        "sd": sd,
        "cov": sd / mean if mean else 0.0,                  # sample sd / mean, as Jetpack's coefficientOfVariation
        "median": quantile(runs, 50),
        "min": min(runs),
        "max": max(runs),
        "p90": quantile(runs, 90),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "qcd": (q3 - q1) / (q3 + q1) if q3 + q1 else 0.0,
    }


def headline(summary, mode="auto", mean_up_to_cov_percent=5.0):
    """Which statistic leads for a case. Both stay in the summary; this only picks the one shown first."""
    if mode == "median" or mode == "mean":
        return mode
    if mode != "auto":
        raise ValueError(f"headline must be auto, median or mean, not {mode!r}")
    return "mean" if summary["cov"] * 100 <= mean_up_to_cov_percent else "median"


def spread(summary, lead):
    """The spread that goes with the leading statistic: sd for the mean, IQR for the median."""
    return summary["sd"] if lead == "mean" else summary["iqr"]
