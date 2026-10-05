# quick-bench

A JVM stand-in for the Jetpack harness, so the vertical flow can be run end to end today:
`probe → trial → inventory → effective → prepare → measure → analyse`.

It measures the same prepared cases the device harness will: real keys, real inputs, bound parameters,
a pool of `fresh(n)` specs drawn before timing, warmup, then `harness.iterations` runs per case (5 when it is not set).
Timing only — allocation counts and CPU counters are Jetpack's, on a device.

When a `benchmark.json` carries a count metric (`allocationCount`, a CPU event) besides `timeNs`, `charts.py` also draws `<metric>-bars_*.png`
(median, min-max whiskers, n shown: with 5 runs a quartile is noise) and adds a per-metric table to `summary.md`;
`analyze.py` adds `<metric>-vs-time.png`. A time-only file produces exactly the output it did before.
An explicit `analysis.charts` list without `countBars` turns the count charts off.

```
cd tools/jca-contract && ./gradlew run --args="../../results/discovery ../../results/configuration ../../config/global-quick.yaml"
cd ../quick-bench   && ./../jca-contract/gradlew run --args="<capture> <trial> ../../results/configuration/effective.yaml ../../results/benchmark"
python3 analyze.py ../../results/benchmark/benchmark.json ../../results/analysis ../../results/configuration/effective.yaml ../../results/preparation/prepared.yaml
python3 charts.py ../../results/benchmark/benchmark.json ../../results/preparation/prepared.yaml ../../results/configuration/effective.yaml ../../results
```

Output: `results/benchmark/benchmark.json`; `analyze.py` writes `results/analysis/{throughput.png,latency.png,stability.png}`;
`charts.py` writes `results/chart/<run-id>/` (`summary.md`, `chart-data.json`, `manifest.yaml`, one `iqr-bars_*.png` per group, operation and input size),
following `analysis` in `effective.yaml`.

| File | Responsibility |
|---|---|
| `stats.py` | the statistics, one definition each: CoV is sample sd ÷ mean (as Jetpack), quantiles interpolate |
| `charts.py` | entry point: reads, summarises, draws, writes |
| `chart_input.py`, `chart_model.py`, `chart_draw.py`, `chart_report.py` | what is read; one case summarised; matplotlib only; summary, data and manifest |
| `analyze.py` | the run-level charts: throughput, latency, stability. Reads `analysis.charts` and the CoV limit from `effective.yaml`; uses `stats.py`, so its CoV is sample sd ÷ mean like everything else |

