# harness

The instrumentation app that probes, prepares and measures on a device. Device run steps: `docs/run.md`. File map: [index.md](index.md).

## Build

| setting | value |
|---|---|
| namespace | `io.github.junekim0007.cryptobench` |
| SDK | compileSdk 36, minSdk 26, targetSdk 36 |
| runner | `androidx.benchmark.junit4.AndroidBenchmarkRunner` |
| test build type | `release`, signed with the debug key, minify off |
| native | NDK 29.0.14206865; CMake 3.22.1 builds `src/main/cpp/CMakeLists.txt` |
| dependencies | benchmark-junit4 1.5.0 (app and androidTest), `:benchmark`, `:environment:discovery`, androidx.test:runner 1.5.2, junit 4.13.2 |
| manifest | `allowBackup=false` |

## Device directories

| directory | holds |
|---|---|
| `getExternalFilesDir(null)/cryptobench` (`/sdcard/Android/data/<package>/files/cryptobench`) | pushed plan inputs; capture, trial, skipped, prepared, `cpu-pins.yaml`, `energy-dry.yaml`, `cov-probe.yaml` |
| `/sdcard/Android/media/<package>` | androidx output |

## Tests

| class | does |
|---|---|
| `DeviceProbe` | installs the bundled providers of the `bundledProviders` argument, then writes this device's capture, classes file and trial via `Discovery`; run alone |
| `DevicePlan` | installs the `bundledProviders` of `effective.yaml`, then prepares and checks the plan on the device |
| `CryptoBenchmark` | one parameterised test per timed case; test name = case id |
| `EnergyDryBenchmark` | one parameterised test per dry energy case: `docs/energy.md` |
| `CovProbe` | timing experiment; arguments `ops` (default 1000000), `runs` (20), `warmupSeconds` (2.0); writes `cov-probe.yaml` |

## DevicePlan

| step | rule |
|---|---|
| inputs | `effective.yaml` required: `missing_file: ..., push effective.yaml with the capture and the trial`; newest `probe_*` and `trial_*` via discovery's `ProbeDirectory`; none: `missing_file: <dir>/<prefix>_<stamp>.yaml` |
| prepare | `Preparation` writes `skipped.yaml` and `prepared.yaml` into the device directory |
| check | `PlanCheck` with `energy.yaml` from the device directory; any refusal throws `RefusedPlanException` |
| timed cases | `harness.energy.capture` other than `dry` |
| dry cases | `harness.energy.capture` = `dry` |

Capture and trial come from the same device; preparation enforces the pair by `capturedAtMillis`.

## CryptoBenchmark

```
CaseRuns.timed { benchmarkRule.measureRepeated { BlackHole.consume(invocation.perIteration() ?: Unit) } }
```

`JetpackConfig` maps `CaseSettings` to `MicrobenchmarkConfig`:

| CaseSettings | MicrobenchmarkConfig |
|---|---|
| `profiling` NONE | profiler null |
| `profiling` METHOD_TRACING | `ProfilerConfig.MethodTracing` |
| `profiling` STACK_SAMPLING | `ProfilerConfig.StackSampling` |
| `warmupIterations` | `warmupCount` |
| `iterations` | `measurementCount` |

Result conversion to `benchmark.json`: `modules/benchmark/docs/measure.md#jetpack-conversion`.

## Core pinning

`cpu` setting: [settings.md](../../settings/docs/settings.md#device-support).

| step | failure |
|---|---|
| core is an index | `unresolved` |
| affinity library loaded | `no_pinning` |
| current affinity readable | `affinity_unreadable` |
| set affinity | `pin_failed: core <n>, errno <e>` |
| read back | `not_pinned` |
| close restores the previous mask | `cpu_restore_failed: errno <e>; later cases would run pinned`; fails that case |

| rule | value |
|---|---|
| required pin fails | the case fails `cpu_pin_failed: <reason>` |
| `cpu-pins.yaml` | one line per case with `cpu` set: `"<id>": {requested, required, core\|failed}` |
| failed pin | also logged with `Log.w`, tag `cryptobench` |

## Affinity

| rule | value |
|---|---|
| library | `libaffinity.so`, built from `src/main/cpp/affinity.c` |
| `allowed()` | current bitmask, or -1 |
| `allow(mask)` | 0, or errno |
| cores | 0..63 |
| scope | restricts the calling thread only; other processes may still run on that core |
