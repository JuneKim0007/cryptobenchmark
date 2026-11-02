# Results

- `results/` is gitignored.
- `manifest.yaml` is written last by every run.

## Layout

| path | files | when |
|---|---|---|
| `manifest.yaml` | run index | every run |
| `discovery/` | `probe_<stamp>.yaml`, `probe_classes_<stamp>.yaml`, `trial_<stamp>.yaml` | every run |
| `discovery/` | `facts.yaml`; the whole device plan directory | `--device` |
| `discovery/` | `energy.yaml`, `energy-preflight/{rails.pbtx,idle.pftrace,busy.pftrace}` | energy capture |
| `configuration/` | `inventory.yaml`, `effective.yaml`, `report.yaml` | every run |
| `preparation/` | `prepared.yaml`, `skipped.yaml` | `--bench`, `--device` |
| `benchmark/` | `benchmark.json` | `--bench`, `--device`, at least one case not `dry` |
| `benchmark/process-<n>/` | one run's files | `processRepetitions` > 1 |
| `benchmark/` | `benchmarkData.json`, `clocks.yaml`, `cpu-pins.yaml` when written | `--device` |
| `benchmark/` | `energy.json`, `traces/` (`*.perfetto-trace`, `dry.pftrace`), `energy-dry.yaml` | energy capture |
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
| `deviceId` | from the probe's runtime: `<model>-api<sdk>-<hash>` on Android, `host-<os>-jdk<major>-<hash>` on a host; hash = first 8 hex of sha256 over the build fingerprint (host: `java.vendor`, `java.runtime.version`); bundled providers and serials are not in it; a probe without these fields stops with `device_id_fields_missing` |
| `runtime` | `benchmark.json` runtime if measured, else the probe runtime; `cpuLocked` added when clocks exist |
| `providers` | `name`, `precedence`, `serviceCount`, sorted by precedence |
| `files` | stage outputs, paths relative to `results/` |
| `counts` | `prepared` (`prepared.cases`), `skipped` (`skipped.skipped`), `measured` (`benchmark.cases`) |

- `files` keys: `probe`, `trial`, `inventory`, `effective`, `report`, `energyCapability`, `energy`, `clocks`, `cpuPins`, `prepared`, `skipped`, `benchmark`, `processes`; `--harness` adds `scopedPlan`, `scopedInterop`, `scoped`; `--interop` adds `interopPlan`, `interop`.
- A key is absent when its stage did not run.
- `energy`, `clocks`, `cpuPins` are single paths when `processRepetitions` = 1, lists otherwise.

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
