# Tools

- Every Gradle build, `apps/benchmark/cli` and each `tools/*` check, runs through the one wrapper `apps/benchmark/gradlew`.
- Build layout: [architecture.md](architecture.md#tools-builds). Energy tools: [energy.md](energy.md#files).

## cli

`apps/benchmark/cli`: the benchmark's host commands, one build.

| entry | command or arguments | output |
|---|---|---|
| `ProbeKt` (default) | `apps/benchmark/gradlew -p apps/benchmark/cli run --args="<discovery dir> [<configuration dir>] [<global.yaml>] [--reuse]"` | prints capture, classes, trial, inventory, effective paths |
| `ConfigureKt` | `... run -PmainClass=ConfigureKt --args="<probe> <trial> <configuration dir> [<global.yaml>] [--facts=<facts.yaml>]"` | inventory, effective |
| `CheckConfigKt` | `... run -PmainClass=CheckConfigKt --args="<global.yaml>..."` | parses each file and its test set; prints `{global, testSet, bundled}` per file as YAML; nothing written |
| `RuntimeFieldsKt` | `... run -PmainClass=RuntimeFieldsKt` | prints this JVM's runtime fields that the device id uses, as YAML |
| `BenchKt` | `<capture> <trial> <effective.yaml> <output dir> <preparation dir> <order file>` | `prepared.yaml`, `skipped.yaml`; cases prepared in listing order, measured in the order file's, which must name each listed case once (`order_mismatch`); `benchmark.json` rewritten as each case finishes, a case that throws is a `skipped:` line and its skip (stage `benchmark`, `measure_failed`); prints the `benchmark.json` path |
| `ListCasesKt` | `<capture> <trial> <effective.yaml> <preparation dir>` | the effective file's bundled providers installed, then the ids `BenchKt` measures, one per line in listing order; nothing written; a refused plan is `error: refused_plan: ...` |
| `ConvertKt` | `<benchmarkData.json> <prepared.yaml> <output dir> [energy.json] [--metrics=TIME,...] [--thermal=thermal.json] [--uncleaned]` | `benchmark.json` from androidx output; a pass's metrics, each case's temperature; `--uncleaned` for the energy pass, the one pass with no collection between samples; `--metrics` alone reports that set instead of each case's own ([run.md](run.md#recover-a-metric-without-a-device)) |
| `MergeRunsKt` | `<output dir> <benchmark.json>...` | merged `benchmark.json` |
| `MergePassesKt` | `<output dir> <timing benchmark.json> [<metric key>=<benchmark.json> ...]` | one `benchmark.json`, each owned metric from its pass ([measure.md](../apps/benchmark/modules/benchmark/docs/measure.md#pass-merge)) |
| `InteropKt` | `<capture> <trial> <effective.yaml> <interop_plan.yaml> <interop.yaml>` | the effective file's bundled providers installed, then `interop.yaml`; prints its path |
| `CheckDiffKt` | `... run -PmainClass=CheckDiffKt --args="<baseline check.yaml> <current check.yaml>"` | a tool, no pipeline step calls it: every case only in one file and every field that differs ([check.md](../apps/benchmark/modules/benchmark/docs/check.md#baseline-and-diff)); exit 3 on any difference |

- Main class comes from `-PmainClass`, default `ProbeKt`.
- Every main (`Command.kt` `command`): arguments it cannot take print `usage: ...` and exit 2; any failure prints one `error: <message>` and exits 1, never a stack trace; an `Error` (out of memory) ends the JVM as it is.
- `ProbeKt` and `ConfigureKt` without a `global.yaml` argument write no `effective.yaml` and warn `no global.yaml given`.
- `ConfigureKt`: a missing input is `error: missing_file`; warnings print `warning: <w>`, skips `skipped: <s>` to stderr.
- Compiles contract, discovery, settings, records, catalogue, config, preparation and benchmark sources; tests are discovery and config tests, plus `ProviderChoseContractTest`: every discovery `providerChose` key is a preparation `ResolvedParameters.KEYS` key or `fixedValueBytes`; `EffectiveKeysAgreeTest`: an effective.yaml with every key config writes reads through preparation without `unknown_keys`.
- `apps/benchmark/gradlew -p apps/benchmark/cli test` excludes `*ExampleFilesTest` and writes captures to `build/capture`.
- CI `.github/workflows/jca-contract.yml` job `probe`: that test on Java 17, 21, 25 (temurin), fail-fast off; uploads `build/capture/*.yaml` as `capture-java-<N>`.
- `BenchKt` prepares and measures with the host harness: `apps/benchmark/modules/benchmark/docs/measure.md`.

## Standalone tools

Not a pipeline or perf-repair step; each runs on its own.

| tool | doc |
|---|---|
| `apps/benchmark-runner/explain.py` | each resolved setting of a run and its source ([run.md](run.md#appsbenchmark-runnerexplainpy)) |
| `CheckDiffKt` | two `check.yaml` files diffed ([cli](#cli)) |
| `apps/perf-repair/src/perfrepair/validation/catalogue_entry.py` | a catalogue entry's static checks, run by tests ([algorithm-catalogue.md](../apps/perf-repair/docs/algorithm-catalogue.md#static-checks-validationcatalogue_entrypy)) |

## android-api-check

```
apps/benchmark/gradlew -p tools/android-api-check compileKotlin -PandroidJar=<android.jar>
```

- Default jar: `$ANDROID_HOME/platforms/android-36/android.jar`.
- Compiles jca, files, document, contract, discovery, settings, records, catalogue, preparation, benchmark sources with JVM target 1.8, `-no-jdk`, `android.jar` compileOnly.
- CI: job `android-api` in `.github/workflows/jca-contract.yml` on Java 17 with `platforms;android-36`.

## analysis

### analyze.py

```
python3 apps/benchmark-runner/analysis/analyze.py <benchmark.json> <out dir> [<effective.yaml>] [<prepared.yaml>]
```

- Writes `summary.md`; `throughput.png`, `latency.png`, `stability.png` when `analysis.charts` names them.
- Writes `<metric>-vs-time.png` per count metric (such as `allocationCount`) in `benchmark.json`.
- Summary columns: case, op, key, input, mean time in `analysis.units.latency` (default ms/op), throughput in `analysis.units.throughput` (default MB/s; `-` where MB/s or MiB/s has no input size), CoV, outliers; values keep 4 significant figures, so a sub-ms time never reads 0.
- Uses `metrics.timeNs.runs`, else `missing_field: metrics.timeNs.runs for <id>`; statistics on the runs `outliers.py` keeps.
- Stability chart gate: `analysis.statistic.meanUpToCovPercent`, default 5%.
- A row's `variant` follows its op (`ENCRYPT notFixed`) in every table and its name in every chart (both scripts), so an item's two variants are two rows and two series, never one.
- Without `prepared.yaml` the cases have no chart group; a warning says so.

### charts.py

```
python3 apps/benchmark-runner/analysis/charts.py <benchmark.json> <prepared.yaml> <effective.yaml> <device folder>
```

- Output folder: `analysis.dir`, else `<device folder>/chart/<run-id>` (`adhoc` without a run id).
- Writes `summary.md`, `chart-data.json`, `manifest.yaml`.
- Writes `<group id>-<group>/iqr-bars_<operation>_input-<size>.png` per chart group, operation and input size when `analysis.charts` names `iqrBars`.
- Writes `<metric>-bars_*.png` and `chart-data-<metric>.json` per count metric; an explicit `analysis.charts` without `countBars` turns them off.
- Statistics on every run; `manifest.yaml` `auditAgainstJetpack` compares them with the ones androidx reported.
- Payload groups (symmetric cipher, hash, mac) with an input size show `analysis.units.throughput` (default MB/s); the others `analysis.units.latency` per op (default ms/op). Statistics stay on ns/op.

| file | holds |
|---|---|
| `lib/cryptobench/cryptobench/shared/stats/descriptive.py` | per-case statistics: mean, sample SD, CoV (SD / mean), interpolated quantiles, IQR, QCD, headline choice |
| `chart_input.py` | reads benchmark.json, chart groups from prepared.yaml, analysis settings |
| `chart_model.py` | one case summarised in its display unit; count metrics |
| `lib/cryptobench/cryptobench/shared/stats/units.py` | `analysis.units`: ns/op to the latency and throughput units, checked; significant-figure numbers |
| `chart_draw.py` | matplotlib drawing for both scripts |
| `chart_report.py` | `summary.md`, `chart-data*.json`, `manifest.yaml` |

### credibility.py

```
python3 apps/benchmark-runner/analysis/credibility.py <out dir> <benchmark.json of each process>...
```

- Writes `credibility.md`, `credibility.json` and `qq/<case>.png` (a line Q-Q plot per case, one panel per metric).
- Unit of repetition: the process; each contributes one value per case and metric: the median of its `timeNs` runs, its `energyJ` J/op.
- Samples are never pooled across processes: within-process samples are correlated, so pooling overstates n.
- Per case and metric: n; median; 95% distribution-free interval of the median from Binomial(n, 1/2) order statistics (n=50: ranks 18-33, n=36: 12-25) with its exact coverage; CoV across processes; median within-process CoV.
- Normality, alpha 0.05: Shapiro-Wilk p (Royston AS R94) and QQ r, the probability-plot correlation of the sorted values with Blom normal scores, pass when r reaches its 5% critical value; n < 8 reads "not meaningful".
- QQ critical value: the 5% quantile of r over 20000 normal samples of that n, seed 1975 (a Filliben-style PPCC table on Blom scores; matches NIST within 0.002), cached per n.
- Within a process (8 samples or more): median QQ r, the share of processes whose QQ r fails, and the share Shapiro-Wilk rejects.
- Steady state per process: median of the last third over the first third of its samples, and a Mann-Whitney p between them; a process drifts above 5% with p < 0.05; a case is flagged when more than 20% of its processes drift; thirds under 8 samples get no p and are not counted as checked.
- Per fixed/notFixed pair of one id: median ratio notFixed/fixed with a 95% percentile bootstrap interval resampling each side's processes (10000 resamples, seed in the output); Mann-Whitney U two-sided p; Cliff's delta with Romano's labels (negligible < 0.147, small < 0.33, medium < 0.474, large).
- Mann-Whitney: exact distribution when both sides have at most 25 values and nothing ties, otherwise the normal approximation with tie and continuity corrections; the output records which (`exact` or `normal`).
- Fixed and notFixed per-process medians are treated as independent samples, though each process runs both: conservative, since they barely correlate (Spearman -0.19 to 0.23).
- Calculations: `lib/cryptobench/cryptobench/shared/stats/inference.py` and `median_ranks` in `equations.py`.

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
- `python3 tools/module-isolation/names_check.py`: Kotlin's `:files` names against Python's `CONTRACT` and `CONTRACT_PARTS`; no file name written by hand outside the module.

