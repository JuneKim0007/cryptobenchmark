# quick-bench

A JVM stand-in for the Jetpack harness, so the vertical flow can be run end to end today:
`probe → trial → inventory → effective → prepare → measure → analyse`.

It measures the same prepared cases the device harness will: real keys, real inputs, bound parameters,
a pool of `fresh(n)` specs drawn before timing, warmup, then `harness.iterations` runs per case (5 when it is not set).
Timing only — allocation counts and CPU counters are Jetpack's, on a device.

```
cd tools/jca-contract && ./gradlew run --args="../../results/discovery ../../results/configuration ../../config/global-quick.yaml"
cd ../quick-bench   && ./../jca-contract/gradlew run --args="<capture> <trial> ../../results/configuration/effective.yaml ../../results/benchmark"
python3 analyze.py ../../results/benchmark/benchmark.json ../../results/analysis
python3 charts.py ../../results/benchmark/benchmark.json ../../results/preparation/prepared.yaml ../../results/configuration/effective.yaml ../../results
```

Output: `results/benchmark/benchmark.json`; `analyze.py` writes `results/analysis/{summary.md,throughput.png,latency.png,stability.png}`;
`charts.py` writes `results/chart/<run-id>/` (`summary.md`, `chart-data.json`, `manifest.yaml`, one `iqr-bars_*.png` per group, operation and input size),
following `analysis` in `effective.yaml`.

| File | Responsibility |
|---|---|
| `stats.py` | the statistics, one definition each: CoV is sample sd ÷ mean (as Jetpack), quantiles interpolate |
| `charts.py` | entry point: reads, summarises, draws, writes |
| `chart_input.py`, `chart_model.py`, `chart_draw.py`, `chart_report.py` | what is read; one case summarised; matplotlib only; summary, data and manifest |
| `analyze.py` | the older flat script: summary and three charts. Still defines its own CoV (σ ÷ median), which `stats.py` does not |

