# Results

- `results/` is gitignored.
- `manifest.yaml` is written last by every run, atomically: a temporary file beside it, then a rename, so a reader finds the old manifest or the whole new one.

## Device folder

```
<results root>/<device_id>/
  discovery/ configuration/ preparation/ benchmark/ analysis/ chart/ interop/ manifest.yaml
  rows.json measurements.json run_log.json primitives.tsv worthiness-<mode>/ grouping/ summary.json summary.md
  <path_id>/ sites.json app.json ... harness.yaml measured/ report.json report.md
```

perf-repair writes the second and third lines: [artifacts.md](../perf-repair/docs/artifacts.md).

| rule | value |
|---|---|
| `--results` | the root, default `<repo>/results` |
| folder name | `deviceId` of the manifest below, from the probe |
| staging | discovery and configure run in `<root>/.staging-*`, then move in; a run that fails there removes it and changes nothing |
| a finished device | a folder holding `manifest.yaml`; a publish deletes the old manifest first, so a run failing later leaves the folder without one and its partial files for debugging |
| `--discovery` | `overwrite` replaces `discovery/`; `keep` and `reuse` add to it |
| `--interop` | beside a finished run: adds `interopPlan`, `interop` to its manifest, its capture to `discovery/`; `configuration/` and the other keys stay |
| `--harness` | writes `measured/` beside `harness.yaml`, itself laid out as this table's device folder without the device level |
| a killed process | `.staging-*` stays behind; nothing reads it, delete it |
| root under `/tmp`, `/var/tmp`, `/var/folders` or the system temp folder | one line `warning: results_in_temp: ...`; the run goes on |

## Layout

Paths relative to the device folder.

| path | files | when |
|---|---|---|
| `manifest.yaml` | run index | every run |
| `discovery/` | `probe_<stamp>.yaml`, `probe_classes_<stamp>.yaml`, `trial_<stamp>.yaml` | every run |
| `discovery/` | `facts.yaml`; the whole device plan directory | `--device` |
| `discovery/` | `energy.yaml`, `energy-preflight/{rails.pbtx,idle.pftrace,busy.pftrace}` (rails), `energy-preflight/` power profile (manafa) | energy capture |
| `configuration/` | `inventory.yaml`, `effective.yaml`, `report.yaml` | every run |
| `preparation/` | `prepared.yaml`, `skipped.yaml` | `--bench`, `--device` |
| `benchmark/` | `benchmark.json` | `--bench`, `--device`, at least one case not `dry` |
| `benchmark/process-<n>/` | one run's files | `processRepetitions` > 1 |
| `benchmark/` | `benchmarkData.json`, `clocks.yaml`, `cpu-pins.yaml` when written | `--device` |
| `benchmark/` | `energy.json`, `traces/` (`*.perfetto-trace`, `dry.pftrace`), `energy-dry.yaml`; `manafa/` (`manafa.log`, power profile) with `energy.source: manafa` | energy capture |
| `scoped/` | `scoped-plan.yaml`, `scoped-interop.yaml`, `benchmarkData.json`, `prepared.yaml`, `benchmark.json`, `clocks.yaml`; `energy.json`, `traces/` on measured capture | `--harness`: [scoped.md](../modules/android/docs/scoped.md) |
| `interop/` | `interop_plan.yaml` (the plan, copied), `interop.yaml` | `--interop`: [interop.md](../modules/preparation/docs/interop.md) |
| `analysis/` | `summary.md`, `throughput.png`, `latency.png`, `stability.png`, `<metric>-vs-time.png` | with `benchmark.json` |
| `chart/<run-id>/` | `summary.md`, `chart-data.json`, `manifest.yaml`, IQR bars per chart group | with `benchmark.json`; `analysis.dir` moves it |

- Energy file fields: [energy.md](energy.md#outputs).

## manifest.yaml

| field | value |
|---|---|
| `schemaVersion` | 1 |
| `mode` | `host` or `device` |
| `config` | path of the `global.yaml` used |
| `deviceId` | from the probe's runtime: `<model>-api<sdk>-<hash>` on Android, `host-<os>-<arch>-jdk<major>-<hash>` on a host; hash = first 8 hex of sha256 over the build fingerprint (host: `java.vendor`, `java.runtime.version`); bundled providers and serials are not in it; a probe without these fields stops with `device_id_fields_missing` |
| `inputs` | `bundled`: sha256 of `providers.bundled`; `config`: sha256 of `global.yaml` without that list, parsed (comments and key order change nothing), with its `selection.testSet` file, `analysis` left out since it only shows results (`scripts/run_inputs.py`); perf-repair's device stage compares them to decide what reruns |
| `units` | `analysis.units` from `effective.yaml`: `{latency: ms\|us\|ns, throughput: MB/s\|MiB/s\|ops/s}`; every view of the run reads it (charts, summaries, perf-repair's report and renders); absent from a run before it existed, read as `{latency: ms, throughput: MB/s}` |
| `runtime` | `benchmark.json` runtime if measured, else the probe runtime; `cpuLocked` added when clocks exist |
| `providers` | `name`, `precedence`, `serviceCount`, sorted by precedence |
| `files` | stage outputs, paths relative to the device folder |
| `counts` | `prepared` (`prepared.cases`), `skipped` (`skipped.skipped`), `measured` (`benchmark.cases`) |

- `files` keys: `probe`, `trial`, `inventory`, `effective`, `report`, `energyCapability`, `energy`, `clocks`, `cpuPins`, `prepared`, `skipped`, `benchmark`, `processes`; `--harness` adds `scopedPlan`, `scopedInterop`, `scoped`; `--interop` adds `interopPlan`, `interop`.
- A key is absent when its stage did not run.
- `energy`, `clocks`, `cpuPins` are single paths when `processRepetitions` = 1, lists otherwise.
- `problems`: coded lines of what the run survived, absent when there were none: `energy_failed: <message>` ([energy.md](energy.md#outputs)); `not_measured: <id>` for each case of `prepared.yaml` not `dry` that the final `benchmark.json` lacks, whatever lost it (the device run, `ConvertKt`'s `not_in_plan`/`no_metrics`/`not_converted`, `MergeRunsKt`'s `not_merged`, a plan-check refusal in `skipped.yaml`); each is also printed.
- A run whose energy is estimated has a top-level `energy: {source, kind: estimated}`; any other run has no `energy` key.

## clocks.yaml

| field | value |
|---|---|
| `schemaVersion` | 1 |
| `locked` | `true`, `false` or `unknown` |
| `before`, `after` | per core: `core`, `index`, `online`, `governor`, `minKhz`, `maxKhz`, `cpuMaxKhz` |

## facts.yaml

| field | value |
|---|---|
| `schemaVersion` | 1 |
| `os.sdkInt` | device SDK level |
| `rooted` | see [run.md](run.md#device-facts) |
| `cpu.cores` | per core: `core`, `online`, `maxKhz` |
| `pinning` | see [run.md](run.md#device-facts) |
