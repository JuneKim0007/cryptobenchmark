# quick-bench

A JVM stand-in for the Jetpack harness (#33), so the vertical flow can be run end to end today:
`probe → trial → inventory → effective → prepare → measure → analyse`.

It measures the same prepared cases the device harness will: real keys, real inputs, bound parameters,
a pool of `fresh(n)` specs drawn before timing, warmup, then five runs per case.
Timing only — allocation counts and CPU counters are Jetpack's, on a device.

```
cd tools/jca-contract && ./gradlew run --args="../../results/discovery ../../results/configuration ../../config/global-quick.yaml"
cd ../quick-bench   && ./../jca-contract/gradlew run --args="<capture> <trial> ../../results/configuration/effective.yaml ../../results/benchmark"
python3 analyze.py ../../results/benchmark/benchmark.json ../../results/analysis
```

Output: `results/benchmark/benchmark.json`, then `results/analysis/{summary.md,throughput.png,latency.png,stability.png}`.
