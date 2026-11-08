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
| dependencies | benchmark-junit4 1.5.0 (app and androidTest; set once, `benchmarkVersion` in `build.gradle`), `:benchmark`, `:environment:discovery`, androidx.test:runner 1.5.2, junit 4.13.2 |
| manifest | `allowBackup=false` |
| tracebox | `traceboxAssets` copies benchmark-common's `tracebox_*` assets into the test APK; below API 29 androidx runs that binary for its Perfetto trace, and without it every case fails `Unable to start perfetto tracing` |

## Device directories

`DeviceDirectory.plan` (Kotlin) and `directories(sdk)` in `apps/benchmark-runner/device/adb.py` choose them; both read the API level.

| API | plan directory | androidx output |
|---|---|---|
| 29 and above | `externalMediaDirs[0]/cryptobench` (`/sdcard/Android/media/<package>/cryptobench`) | `/sdcard/Android/media/<package>` |
| 26 to 28 | `getExternalFilesDir(null)/cryptobench` (`/sdcard/Android/data/<package>/files/cryptobench`) | `/sdcard/Android/data/<package>/cache` |

| rule | value |
|---|---|
| plan directory holds | pushed plan inputs; capture, trial, skipped, prepared, `cpu-pins.yaml`, `native-cleanup.yaml`, `energy-dry.yaml`, `scoped-interop.yaml` |
| why media from API 29 | API 30 denies `adb shell` any read of `/sdcard/Android/data`; androidx itself writes to the media directory from API 29 |
| androidx output | androidx's own choice per API level; the script only mirrors it |
| no media directory mounted | `no_storage: external storage is not mounted for <package>` |
| `getprop ro.build.version.sdk` not a number | `no_sdk: getprop ro.build.version.sdk printed '<v>'` |

## Tests

| class | does |
|---|---|
| `DeviceProbe` | installs the bundled providers of the `bundledProviders` argument, then writes this device's capture, classes file and trial via `Discovery`; run alone |
| `DevicePlan` | installs the `bundledProviders` of `effective.yaml`, lists and checks the plan on the device; each test prepares only its own case |
| `CryptoBenchmark` | one parameterised test per timed case; test name = case id; `-e case <id>` keeps that case only (`run.isolation: case` starts one process per case: [device-session.md](../../../../../docs/device-session.md#one-process-per-case)) |
| `EnergyDryBenchmark` | one parameterised test per dry energy case: `docs/energy.md` |
| `ScopedInterop` | the scope interop check, alone in its process: [scoped.md](scoped.md) |

## DevicePlan

| step | rule |
|---|---|
| inputs | `effective.yaml` required: `missing_file: ..., push effective.yaml with the capture and the trial`; newest `probe_*` via discovery's `ProbeDirectory`, its `trial_*` by the same stamp; none: `missing_file: ...` |
| list | `RunnablePlan.list`: no key made, no provider called; a process without the `case` argument (the listing, or one process for every case) writes `skipped.yaml` and `prepared.yaml` afresh, a process given cases by name only adds to them |
| prepare | `DevicePlan.prepared(case)` inside the test: a failure is that case's skip in `skipped.yaml`, its entry removed from `prepared.yaml`; `CryptoBenchmark` and `EnergyDryBenchmark` then fail the test (`not_prepared: <skip>`), `EndToEndCheck` records it as notRun |
| check | `PlanCheck.runnable` with `JetpackConfig.METRICS` and `energy.yaml` from the device directory: a refused case is left out and added to `skipped.yaml` (stage `benchmark`, reason `<caseId>: <refusal>`); a run-wide refusal or no case left throws `RefusedPlanException` |
| timed cases | `harness.energy.capture` other than `dry`; with the instrumentation argument `case` (`CaseFilter.ARGUMENT`) only the named ids, in the argument's order |
| dry cases | `harness.energy.capture` = `dry` |

Capture and trial come from the same device; preparation enforces the pair by `capturedAtMillis`.

## CryptoBenchmark

```
JetpackCase.timed: counterMismatch check, then PinnedCase.run { benchmarkRule.measureRepeated { BlackHole.consume(call() ?: Unit); every 50 000th call runWithMeasurementDisabled { GC + finalizers } } }; NativeCleanups.record
```

`JetpackConfig` maps `CaseSettings` to `MicrobenchmarkConfig`:

| CaseSettings | MicrobenchmarkConfig |
|---|---|
| `profiling` NONE | profiler null |
| `profiling` METHOD_TRACING | `ProfilerConfig.MethodTracing` |
| `profiling` STACK_SAMPLING | `ProfilerConfig.StackSampling` |
| `warmupIterations` | `warmupCount` |
| `iterations` | `measurementCount`; a pass's `cryptobench.samples` replaces it |
| a pass (`-e cryptobench.pass timing\|energy\|allocation`) | `PassArguments`: energy capture `none` outside the energy pass; the allocation pass adds `SampledAllocations` to the timed phase's metrics |

`BenchmarkRule` is androidx's public rule; its `measureRepeated` always runs every phase, whatever `run.metrics` says:

| phase | runs | in `benchmark.json` |
|---|---|---|
| timing | always | `timeNs` |
| profiling | when `profiling` is set | no; trace files only |
| allocation | always, 5 runs | `allocationCount` only when `run.metrics` has `ALLOCATION` |
| CPU event counter | `apps/benchmark-runner/device/adb.py` passes `androidx.benchmark.cpuEventCounter.enable=true` when `run.metrics` has `CPU_EVENTS`; config refuses it on an unrooted device: [settings.md](../../settings/docs/settings.md#device-support) | `instructions`, `cpuCycles`, `branchMisses` only when asked |

ALLOCATION not requested: androidx still runs its allocation phase; it is not reported. `run.metrics` selects what is reported, not what runs; the filter is `JetpackResults`: `apps/benchmark/modules/benchmark/docs/measure.md#jetpack-conversion`.

| rule | value |
|---|---|
| rule setup | `GrantPermissionRule` for `WRITE_EXTERNAL_STORAGE`; skipped when `androidx.benchmark.enabledRules` leaves out `Microbenchmark`; skipped on an emulator with `androidx.benchmark.skipBenchmarksOnEmulator=true` |
| thread | `measureRepeated` on the main thread fails |
| profiler | any `profiling` with any `run.metrics`; androidx runs it in its own phase |
| API | public androidx API only; no restricted entry point or lint suppression |

| counter argument vs `run.metrics` | failure when the case runs |
|---|---|
| `CPU_EVENTS` asked, argument not `true` | `not_supported: CPU_EVENTS, the launch argument androidx.benchmark.cpuEventCounter.enable is not true` |
| argument `true`, `CPU_EVENTS` not asked | `not_requested: androidx.benchmark.cpuEventCounter.enable is true but run.metrics has no CPU_EVENTS` |
| argument `true`, androidx drops the counter (unrooted, dry run) | conversion fails `missing_field: metrics.instructions for <id>; ...` |

Result conversion to `benchmark.json`: `apps/benchmark/modules/benchmark/docs/measure.md#jetpack-conversion`.

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
| `native-cleanup.yaml` | one line per timed case: `"<id>": {everyCalls, cleanups, pausedNanos}`, its `NativeBudget` ([native-budget.md](../../benchmark/docs/native-budget.md)) |

## Affinity

| rule | value |
|---|---|
| library | `libaffinity.so`, built from `src/main/cpp/affinity.c` |
| `allowed()` | current bitmask, or -1 |
| `allow(mask)` | 0, or errno |
| cores | 0..63 |
| scope | restricts the calling thread only; other processes may still run on that core |
