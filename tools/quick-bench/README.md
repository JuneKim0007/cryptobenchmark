# quick-bench

Host (JVM) prepare, measure and analyse over the same prepared cases the device harness runs; timing only.
`python3 scripts/pipeline.py --bench` runs these steps; by hand, from `tools/quick-bench`:

```
../jca-contract/gradlew -p ../jca-contract run --args="../../results/discovery ../../results/configuration ../../config/global-quick.yaml"
../jca-contract/gradlew run --args="<capture> <trial> ../../results/configuration/effective.yaml ../../results/benchmark ../../results/preparation"
python3 analyze.py ../../results/benchmark/benchmark.json ../../results/analysis ../../results/configuration/effective.yaml ../../results/preparation/prepared.yaml
python3 charts.py ../../results/benchmark/benchmark.json ../../results/preparation/prepared.yaml ../../results/configuration/effective.yaml ../../results
```

Arguments, outputs, the outlier filter and the chart files: [docs/tools.md](../../docs/tools.md).
