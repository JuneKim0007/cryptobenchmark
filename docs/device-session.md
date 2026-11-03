# Device session

How a `--device` run measures: one session, its passes, its processes. Flags and steps: [run.md](run.md).

## Session

`scripts/measure_session.py` runs every measuring session on a device, for the benchmark (`CryptoBenchmark`) and the before/after run (`ScopedBenchmark`, [scoped.md](../modules/android/docs/scoped.md)); a path gives only its plan: the test class, the cases, how a process's files are pulled and converted.

| step | what runs |
|---|---|
| session | `processRepetitions` processes (folders `process-<n>/` when above 1), merged by `MergeRunsKt` |
| process | clear the device's outputs; one `am instrument` per case (`isolation: case`) or one for all (`run`); pull `benchmarkData.json`, the plan files and `cpu-pins.yaml`; convert with `ConvertKt` |
| hooks | around the session, each process and each case: the clock state and the energy window (`scripts/session_hooks.py`) |

## Passes

`run.passes` ([config.md](../modules/config/docs/config.md)) splits a device run into one session per metric group; without it one pass measures every metric, as before.

| pass | measures | samples | energy | device time per case (Pixel 10, about 0.11 s a sample) |
|---|---|---|---|---|
| `timing` | `TIME` (and `CPU_EVENTS`) | `samples` override every `iterations` | none: no window, no trace pulled | 300: about 34 s timed + about 4 s warm-up, allocation phase and process start = about 38 s |
| `energy` | `TIME` (dropped at the merge) and `energyJ` | `samples` set the timed phase, which is the energy window (`windowSeconds` applies only to `dry`) | the case's own capture (`measured`); rails pre-flight once per run | 100: about 11 s + `energy.cooldownSeconds` (5) + 4 = about 20 s |
| `allocation` | `ALLOCATION`, one run per sample (`SampledAllocations` inside the timed phase; androidx's own phase keeps its 5) | as `timing` | none | 100: about 11 s, counting slows each sample (not measured yet), + 4 = 15 to 30 s |

- Per group: timing takes many short samples with no trace pulled; energy takes a window of about 100 rail polls; allocation counting slows the timed loop, and those times never reach the results.
- Merge: the timing pass's rows are the base; `MergePassesKt` takes `energyJ` only from the energy pass and `allocationCount` only from the allocation pass. A case a pass lost has no value of that metric (`not_merged: <id>: <key>: its pass has no row`), never the timing pass's, so a metric's before/after pair always comes from one pass and drift between passes never enters a ratio.
- Layout: `benchmark/<pass>/` (with `process-<n>/` under it), then `benchmark/benchmark.json` merged; with repetitions also `benchmark/process-<n>/benchmark.json`, the n-th process of every pass merged, which `manifest.yaml` lists as `processes`. The before/after run does the same under `scoped/`.
- Each pass prints `pass:      <name> pass: <n> processes, <time> on the device`; the run's device time is their sum, plus thermal sleeps (31% of the last full Pixel session).
- `capture: dry` with `run.passes` stops with `not_supported`; an energy pass with no `measured` case is skipped with a warning; `--bench` warns and measures once per process.

## Temperature

`scripts/thermal.py` reads `adb shell dumpsys thermalservice`, which an unrooted shell may run (`/sys/class/thermal` is denied to it on the Pixel); `scripts/thermal_hook.py` reads it before and after every process and every case, in the benchmark and the before/after run.

| rule | value |
|---|---|
| sensors | every `Temperature{mValue, mType, mName, mStatus}` line, keyed by the HAL's `mName`; a value outside -60..200 C (the HAL's `-3.4e38` for unknown, `NaN`) is no reading |
| status | `Thermal Status: <n>`, 0 none to 6 shutdown |
| section | `Current temperatures from HAL:` (queried when dumpsys runs); when absent or empty, `Cached temperatures:` with note `source: cached` |
| unavailable | `start`, `end`, statuses null and the reason in `thermalNote`; the case is measured as ever |
| `isolation: run` | no case boundary: every case gets its process's reading, note `scope: run` |
| files | `thermal.json` per process folder (`process` and `cases`); `ConvertKt --thermal` puts each case's reading in `benchmark.json` ([results.md](results.md#benchmarkjson-case-fields)) |
| per pass | `thermal:   <pass>: hottest <c> C at a case start, <c> C at an end; <n> pauses, <s> s paused; <n> cases ended throttled (status > 0)` |
| cost | two `dumpsys` calls per case, under a second |

- Cached values: AOSP's `ThermalManagerService` fills `Cached temperatures` only from the HAL's `onTemperatureChanged` callbacks, which a HAL sends when a sensor's severity changes; between changes the cached value can be minutes old. The `Current temperatures from HAL` section asks the HAL at dump time. Whether the Pixel's Android 17 dump to an unrooted shell carries that section is not yet confirmed on the phone; when it does not, every reading is noted `source: cached` and is a lower bound on how stale the temperature is.

## One process per case

`run.isolation` ([config.md](../modules/config/docs/config.md)) decides how `CryptoBenchmark` runs; the run prints one line saying which.

| `run.isolation` | printed | what runs |
|---|---|---|
| `case` (default) | `measure:   one process per case (<n> cases, isolation: case)` | `-e log true` lists the planned timed cases without running them, then one `am instrument -e case <id>` per case; each process writes its own `benchmarkData.json`, pulled after it and joined into one (the first process's `context`, every process's `benchmarks`) |
| `run` | `measure:   one process for every case (isolation: run)` | one `am instrument` holding every timed case |

- Device time: a process per case costs about 1 to 2 s of instrumentation start plus the plan's preparation on the device, per case and per pass.

- Why: a provider that leaks native memory across calls can abort its process (seen: a bundled provider's HMAC throwing `std::bad_alloc` after many `doFinal` calls on one reused `Mac`). In one process that ends every case after it; with a process per case the OS reclaims the memory when the case's process exits, and only that case is lost.
- Cost: each case pays an instrumentation start, about 1–2 s against about 60 s of measuring, and the device prepares the whole plan again in every process (`DevicePlan` has no per-case preparation), so a plan whose keys are slow to generate pays that per case too.
- A case whose process fails (`Process crashed.`, a failed test, no `benchmarkData.json`) or passes the `case` ceiling ([Timeouts](run.md#timeouts); the app is force-stopped before the next case) prints `case_failed: <id>: <reason>`, goes to `manifest.yaml` `problems`, and the run goes on; every case failing raises.
- `isolation: run`: `CryptoBenchmark` partial failures become warnings; all failed raises.
- Energy: the rails pre-flight runs once per run, after the plan push and AOT compile, never per process; `measured` keeps one Jetpack trace per case either way; `EnergyDryBenchmark`, `ScopedBenchmark`, `InteropCheck` and `DeviceProbe` stay one process each.

