# Tools

- Every Gradle build, `apps/benchmark/cli` and each `tools/*` check, runs through the one wrapper `apps/benchmark/gradlew`.
- Build layout: [architecture.md](architecture.md#tools-builds). Energy tools: [energy.md](energy.md#files).

## cli

`apps/benchmark/cli`: the benchmark's host commands, one build.

| entry | command or arguments | output |
|---|---|---|
| `ProbeKt` (default) | `apps/benchmark/gradlew -p apps/benchmark/cli run --args="<discovery dir> [<configuration dir>] [<global.yaml>] [--reuse]"` | prints capture, classes, trial, inventory, effective paths |
| `ConfigureKt` | `... run -PmainClass=ConfigureKt --args="<probe> <trial> <configuration dir> [<global.yaml>] [--facts=<facts.yaml>]"` | inventory, effective |
| `CheckConfigKt` | `... run -PmainClass=CheckConfigKt --args="<global.yaml>..."` | parses each file and its test set; prints `{global, testSet, bundled}` per file as YAML; a refusal is `error: <message>`, exit 1; nothing written |
| `RuntimeFieldsKt` | `... run -PmainClass=RuntimeFieldsKt` | prints this JVM's runtime fields that the device id uses, as YAML |
| `examples.ParametersKt` | no args, or one spec class | lists `AlgorithmParameterSpec` classes in `java.security.spec` and `javax.crypto.spec`; with a class, prints a parameters YAML block |
| `examples.ReportKt` | `<type> <algorithm> <provider>`, default `Cipher AES SunJCE` | who serves the type and algorithm on this JVM |
| `examples.TreeKt` | none | markdown tree for Cipher, MessageDigest, Mac, Signature, KeyGenerator, KeyPairGenerator, KeyAgreement; source of `apps/benchmark/modules/environment/discovery/docs/tree.md` |
| `BenchKt` | `<capture> <trial> <effective.yaml> <output dir> <preparation dir>` | `prepared.yaml`, `skipped.yaml`; prints the `benchmark.json` path |
| `ConvertKt` | `<benchmarkData.json> <prepared.yaml> <output dir> [energy.json] [--metrics=TIME,...] [--samples=n] [--thermal=thermal.json]` | `benchmark.json` from androidx output; a pass's metrics and samples, each case's temperature; `--metrics` alone reports that set instead of each case's own ([run.md](run.md#recover-a-metric-without-a-device)) |
| `MergeRunsKt` | `<output dir> <benchmark.json>...` | merged `benchmark.json` |
| `MergePassesKt` | `<output dir> <timing benchmark.json> [<metric key>=<benchmark.json> ...]` | one `benchmark.json`, each owned metric from its pass ([measure.md](../apps/benchmark/modules/benchmark/docs/measure.md#pass-merge)) |
| `InteropKt` | `<capture> <trial> <interop_plan.yaml> <interop.yaml>` | `interop.yaml`; prints its path |

- Main class comes from `-PmainClass`, default `ProbeKt`.
- `ProbeKt` and `ConfigureKt` fall back to the nearest `config/global.yaml` up the tree; none found gives a warning and no `effective.yaml`.
- `ConfigureKt`: fewer than 3 paths exits 2; a missing input prints `error: missing_file`, exits 1; warnings print `warning: <w>`, skips `skipped: <s>` to stderr.
- Compiles discovery, settings, config, preparation and benchmark sources; tests are discovery and config tests, plus `ProviderChoseContractTest`: every discovery `providerChose` key is a preparation `ResolvedParameters.KEYS` key or `fixedValueBytes`.
- `apps/benchmark/gradlew -p apps/benchmark/cli test` excludes `*ExampleFilesTest` and writes captures to `build/capture`.
- CI `.github/workflows/jca-contract.yml` job `probe`: that test on Java 17, 21, 25 (temurin), fail-fast off; uploads `build/capture/*.yaml` as `capture-java-<N>`.
- `BenchKt` prepares and measures with the host harness: `apps/benchmark/modules/benchmark/docs/measure.md`.

## android-api-check

```
apps/benchmark/gradlew -p tools/android-api-check compileKotlin -PandroidJar=<android.jar>
```

- Default jar: `$ANDROID_HOME/platforms/android-36/android.jar`.
- Compiles discovery, settings, preparation, benchmark sources with JVM target 1.8, `-no-jdk`, `android.jar` compileOnly.
- CI: job `android-api` in `.github/workflows/jca-contract.yml` on Java 17 with `platforms;android-36`.

## quick-bench analysis

### analyze.py

```
python3 tools/quick-bench/analyze.py <benchmark.json> <out dir> [<effective.yaml>] [<prepared.yaml>]
```

- Writes `summary.md`; `throughput.png`, `latency.png`, `stability.png` when `analysis.charts` names them.
- Writes `<metric>-vs-time.png` per count metric (`allocationCount`, a CPU event) in `benchmark.json`.
- Summary columns: case, op, key, input, mean time in `analysis.units.latency` (default ms/op), throughput in `analysis.units.throughput` (default MB/s; `-` where MB/s or MiB/s has no input size), CoV, outliers; values keep 4 significant figures, so a sub-ms time never reads 0.
- Uses `metrics.timeNs.runs`, else `missing_field: metrics.timeNs.runs for <id>`; statistics on the runs `outliers.py` keeps.
- Stability chart gate: `analysis.statistic.meanUpToCovPercent`, default 5%.
- A row's `variant` follows its op (`ENCRYPT notFixed`) in every table and its name in every chart (both scripts), so an item's two variants are two rows and two series, never one.
- Without `prepared.yaml` the cases have no chart group; a warning says so.

### charts.py

```
python3 tools/quick-bench/charts.py <benchmark.json> <prepared.yaml> <effective.yaml> <device folder>
```

- Output folder: `analysis.dir`, else `<device folder>/chart/<run-id>` (`adhoc` without a run id).
- Writes `summary.md`, `chart-data.json`, `manifest.yaml`.
- Writes `<group id>-<group>/iqr-bars_<operation>_input-<size>.png` per chart group, operation and input size when `analysis.charts` names `iqrBars`.
- Writes `<metric>-bars_*.png` and `chart-data-<metric>.json` per count metric; an explicit `analysis.charts` without `countBars` turns them off.
- Statistics on every run; `manifest.yaml` `auditAgainstJetpack` compares them with the ones androidx reported.
- Payload groups (symmetric cipher, hash, mac) with an input size show `analysis.units.throughput` (default MB/s); the others `analysis.units.latency` per op (default ms/op). Statistics stay on ns/op.

| file | holds |
|---|---|
| `stats.py` | per-case statistics: mean, sample SD, CoV (SD / mean), interpolated quantiles, IQR, QCD, headline choice |
| `chart_input.py` | reads benchmark.json, chart groups from prepared.yaml, analysis settings |
| `chart_model.py` | one case summarised in its display unit; count metrics |
| `display_units.py` | `analysis.units`: ns/op to the latency and throughput units, checked; significant-figure numbers |
| `chart_draw.py` | matplotlib drawing for both scripts |
| `chart_report.py` | `summary.md`, `chart-data*.json`, `manifest.yaml` |

### outliers.py

- A run is an outlier at Z = 3.0 sample SDs from the mean of the other runs.
- Drops the farthest outlier one at a time.
- More than 20 drops keeps every run.

## module-isolation

| command | effect |
|---|---|
| `apps/benchmark/gradlew -p tools/module-isolation test` | all subprojects |
| `apps/benchmark/gradlew -p tools/module-isolation :config:test` | one subproject |
| `apps/benchmark/gradlew -p tools/module-isolation test -Dexamples.update=true` | regenerates `example/` outputs |

- Subprojects and classpaths: [architecture.md](architecture.md#isolation-build).

