"""Whether androidx's warm-up left a case a usable sample: it sets calls per sample from a moving average one stall can inflate, down to one call."""
import json
import statistics

SHORT_SAMPLE_MS = 1.0       # androidx targets about 100 ms; the collapsed samples seen on a Pixel 10 were under 0.1 ms
WARMUP_NEAR_CAP_S = 6.0     # androidx ends a warm-up at 8 s whether or not the timing has settled; it does not report which happened


def _benchmarks(data_file):
    return json.loads(data_file.read_text())["benchmarks"]


def _sample_ms(benchmark):
    return benchmark["repeatIterations"] * statistics.median(benchmark["metrics"]["timeNs"]["runs"]) / 1e6


def short_samples(data_file):
    """One coded line per benchmark whose calls per sample collapsed."""
    return [f"miscalibrated: {b['name']}: {b['repeatIterations']} calls per sample, {_sample_ms(b):.3f} ms a sample"
            for b in _benchmarks(data_file) if _sample_ms(b) < SHORT_SAMPLE_MS]


def near_cap(data_file):
    """One line per benchmark whose warm-up probably ran out of time instead of settling."""
    lines = []
    for b in _benchmarks(data_file):
        seconds = b["warmupIterations"] * statistics.median(b["metrics"]["timeNs"]["runs"]) / 1e9
        if seconds >= WARMUP_NEAR_CAP_S and _sample_ms(b) >= SHORT_SAMPLE_MS:
            lines.append(f"note: warmup_near_cap: {b['name']}: about {seconds:.1f} s")
    return lines
