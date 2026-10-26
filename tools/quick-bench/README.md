# quick-bench

Host (JVM) prepare, measure and analyse over the same prepared cases the device harness runs; timing only.
`python3 scripts/pipeline.py --bench` runs these steps; by hand, from `tools/quick-bench`:

```
../jca-contract/gradlew -p ../jca-contract run --args="../../results/discovery ../../results/configuration ../../config/global-quick.yaml"
../jca-contract/gradlew run --args="<capture> <trial> ../../results/configuration/effective.yaml ../../results/benchmark ../../results/preparation"
python3 analyze.py ../../results/benchmark/benchmark.json ../../results/analysis
```

Arguments, outputs and the outlier filter: [docs/tools.md](../../docs/tools.md).
