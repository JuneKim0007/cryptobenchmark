# analysis

Analysis of a `benchmark.json`: summary, charts and statistics; the host prepare and measure it follows is `BenchKt` in `apps/benchmark/cli`.
`python3 apps/benchmark-runner/pipeline.py --bench` runs these steps; by hand, from the repository root, with `results/x` for a device folder:

```
python3 apps/benchmark-runner/analysis/analyze.py results/x/benchmark/benchmark.json results/x/analysis results/x/configuration/effective.yaml results/x/preparation/prepared.yaml
python3 apps/benchmark-runner/analysis/charts.py results/x/benchmark/benchmark.json results/x/preparation/prepared.yaml results/x/configuration/effective.yaml results/x
```

Arguments, outputs, the outlier filter and the chart files: [docs/tools.md](../../../docs/tools.md).
