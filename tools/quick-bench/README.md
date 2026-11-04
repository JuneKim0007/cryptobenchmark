# quick-bench

Host (JVM) prepare, measure and analyse over the same prepared cases the device harness runs; timing only.
`python3 scripts/pipeline.py --bench` runs these steps; by hand, from `tools/quick-bench`, with `results/x` for a device folder:

```
../../gradlew -p ../jca-contract run --args="../../results/x/discovery ../../results/x/configuration ../../config/global-quick.yaml"
../../gradlew run --args="<capture> <trial> ../../results/x/configuration/effective.yaml ../../results/x/benchmark ../../results/x/preparation"
python3 analyze.py ../../results/x/benchmark/benchmark.json ../../results/x/analysis ../../results/x/configuration/effective.yaml ../../results/x/preparation/prepared.yaml
python3 charts.py ../../results/x/benchmark/benchmark.json ../../results/x/preparation/prepared.yaml ../../results/x/configuration/effective.yaml ../../results/x
```

Arguments, outputs, the outlier filter and the chart files: [docs/tools.md](../../docs/tools.md).
