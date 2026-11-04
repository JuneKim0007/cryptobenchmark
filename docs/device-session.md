# Device session

How a `--device` run measures: one session, its passes, its processes. Flags and steps: [run.md](run.md).

## Session

`scripts/session/measure.py` runs every measuring session on a device, for the benchmark (`CryptoBenchmark`) and the before/after run (`ScopedBenchmark`, [scoped.md](../modules/android/docs/scoped.md)); a path gives only its plan: the test class, the cases, how a process's files are pulled and converted.

| step | what runs |
|---|---|
| session | `processRepetitions` processes (folders `process-<n>/` when above 1), merged by `MergeRunsKt`; a case whose processes hold unequal run counts of a metric is not merged (`not_merged: <id>: unequal_samples: ...`), and a runtime value another process reports differently is one `runtime_differs: <key>: ...` line, the first kept |
| process | clear the device's outputs; one `am instrument` per case (`isolation: case`) or one for all (`run`); pull `benchmarkData.json`, the plan files and `cpu-pins.yaml`; convert with `ConvertKt` |
| hooks | around the session, each process and each case: the cool-down (`scripts/session/cooldown_hook.py`), the thermal gate (`scripts/session/thermal_gate.py`, [Thermal gate](#thermal-gate)), the clock state (`scripts/session/clocks_hook.py`), the energy window (`scripts/session/energy_hook.py`), the temperature (`scripts/session/thermal_hook.py`) |

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

## Variants

`run.variants` ([operations.md](../modules/preparation/docs/operations.md#variants)): the device prepares one case per variant of each item; `scripts/session/variant_order.py` orders the benchmark's cases, never the before/after run's (`alternating`, by scope pair).

| rule | value |
|---|---|
| order | items as the plan lists them; an item's `fixed` and `notFixed` cases adjacent, `fixed` first in odd repetitions and `notFixed` first in even ones (A/B, then B/A: A/B/B/A over two) |
| item | the case id without its last part `_fixed` or `_notFixed` |
| process | `isolation: case`: each variant in its own process, so heap and JIT state never pass between them; `isolation: run` runs both in one process, in plan order |
| same inputs | both from the same seed and key recipe; setup, inputs and buffers before the timer |
| cost | about 2x the device cases of an item that has two variants; key generation has one |

## Temperature

`scripts/device/thermal.py` reads `adb shell dumpsys thermalservice`, which an unrooted shell may run (`/sys/class/thermal` is denied to it on the Pixel); `scripts/session/thermal_hook.py` reads it before and after every process and every case, in the benchmark and the before/after run.

| rule | value |
|---|---|
| sensors | every `Temperature{mValue, mType, mName, mStatus}` line, keyed by the HAL's `mName`; a value outside -60..200 C (the HAL's `-3.4e38` for unknown, `NaN`) is no reading |
| status | `Thermal Status: <n>`, 0 none to 6 shutdown |
| section | `Current temperatures from HAL:` (queried when dumpsys runs); when absent or empty, `Cached temperatures:` with note `source: cached` |
| unavailable | `start`, `end`, statuses null and the reason in `thermalNote`; the case is measured as ever |
| `isolation: run` | no case boundary: every case gets its process's reading, note `scope: run` |
| files | `thermal.json` per process folder (`process` and `cases`; with the gate on also its `gate` baseline and each case's `gate`); `ConvertKt --thermal` puts each case's reading in `benchmark.json` ([results.md](results.md#benchmarkjson-case-fields)) |
| per pass | `thermal:   <pass>: hottest <c> C at a case start, <c> C at an end; <n> pauses, <s> s paused; <n> cases ended throttled (status > 0)` |
| cost | two `dumpsys` calls per case, under a second |
| Jetpack's heat pause | `run.thermalThrottleSleepSeconds` passed as `-e androidx.benchmark.thermalThrottle.sleepDurationSeconds` to every measuring process; unset keeps Jetpack's 90 s |

- Cached values: AOSP's `ThermalManagerService` fills `Cached temperatures` only from the HAL's `onTemperatureChanged` callbacks, which a HAL sends when a sensor's severity changes; between changes the cached value can be minutes old. The `Current temperatures from HAL` section asks the HAL at dump time. Whether the Pixel's Android 17 dump to an unrooted shell carries that section is not yet confirmed on the phone; when it does not, every reading is noted `source: cached` and is a lower bound on how stale the temperature is.

## Cool-down and frequency caps

| rule | value |
|---|---|
| cool-down | `run.caseCooldownSeconds` (0): the host sleeps before every measured case but each session's first, before the case's temperature and clocks are read; `isolation: run` has no case boundary, so it sleeps between processes |
| printed | `cool-down: <pass>: <n> x <s> s = <t> s between cases` per pass when set |
| with the gate | the cool-down sleeps first, then `run.thermalGate` waits while the device is above its target ([Thermal gate](#thermal-gate)) |
| cost | `(cases - 1) x seconds` per pass; at 20 s and 50 cases about 16 min a pass |
| caps | `clocks.yaml` `cases`: per case the online cores whose `scaling_max_freq` is below `cpuinfo_max_freq` at its start and end; `clocks:    <n> of <m> cases started or ended with a core capped below its maximum` per process |
| what caps show | boundary snapshots, one sysfs read each (tens of ms); a cap that rose and fell inside a case is not seen; unrooted, a cap cannot be lifted, only recorded |
| pinning | `run.harness.cpu.core` (`<index>` or `big`) pins the measuring thread on both paths ([harness.md](../modules/android/docs/harness.md#core-pinning)); a failed pin is `cpu_pin_failed` in `cpu-pins.yaml` and a warning |

## Thermal gate

Why: a case that starts on a device still hot from the last one runs on throttled clocks, so its time reads slower than the same case on a cool device; a fixed cool-down guesses how long cooling takes, the gate reads it.

| rule | value |
|---|---|
| on | `run.thermalGate` set and not `enabled: false` ([config.md](../modules/config/docs/config.md)); absent, every case starts as soon as the last ends |
| baseline | once per run, before the warm-up and the first case (after the energy pre-flight's idle settle): the hottest of `sensors` (`scripts/device/thermal.py`); target = baseline + `marginCelsius`; printed `gate:      baseline <c> C, the hottest of <sensors>; a case starts at or below <t> C and status 0`, recorded in each `thermal.json` as `gate: {sensors, baseline, target}` |
| wait | before each case process (`isolation: case`), or before each process (`isolation: run`, no case boundary): read every `pollSeconds` while the hottest of `sensors` is above target or `Thermal Status` is above 0 |
| timeout | past `timeoutSeconds` the case starts anyway; `thermal_gate_timeout: <id>: <pass>: started after <s> s at <c> C, status <n>, target <t> C` in `manifest.yaml` `problems` (`process-<n>` for `isolation: run`) |
| sensors | names in config (device facts), never in code; one absent from a reading is skipped; none present at the baseline turns the gate off for the run with one `warning: thermal_gate_off: ...`; a poll with no gated sensor and no status does not hold a case |
| order | `caseCooldownSeconds` first (fixed), then the gate, then the case's temperature and clocks are read; the warm-up is not gated; the before/after run is gated the same way |
| record | `benchmark.json` per case: `gate: {waitedSeconds, target, timedOut}` ([results.md](results.md#benchmarkjson-case-fields)) |
| per pass | `gate:      <pass>: <n> of <m> cases gated, <s> s waited, max <s> s, <n> timed out` |
| `--bench` | no temperatures on a host: one `warning: thermal_gate_off: ...` and the run measures ungated |
| cost | unknown until measured on the phone; worst case `timeoutSeconds x cases` per pass (the overnight 120 s x about 285 cases = about 9.5 h a pass); one `dumpsys` per poll |

What it does not fix:
- heat inside a case: the timed loop is untouched, so a long case still warms the device while it measures, and Jetpack's own heat pause still applies.
- a hot idle: the baseline is the device before the warm-up, not a cold device; a run started warm gates to a warm target. Read after the warm-up it was 50 C while every Pixel 10 case started at 43-45 C, so the gate never waited.
- skin and battery heat: only the named sensors and the status count; a warm battery under a cool CPU does not wait.
- stale readings: with only `Cached temperatures` ([Temperature](#temperature)) the gate can see an old value and start or wait wrongly.
- frequency caps: a cap the governor keeps after the device cools is recorded in `clocks.yaml`, never waited out.

## Warm-up

`run.warmup` ([config.md](../modules/config/docs/config.md)): one process before the first pass of a session, on any device path, the benchmark and the before/after run alike.

| rule | value |
|---|---|
| what it is | a pre-flight check that the app, the providers and the timed loop run on this device; not temperature stabilisation, and no number of it is kept |
| cases | `jobs`: test-set rules `{provider?, type?, name?}` against the planned cases (`name` a glob on the algorithm, case-insensitive); `[]` the plan's first 3 |
| samples | `iterations` (10) per case, as `-e cryptobench.pass warmup`: no energy capture |
| output | deleted on the device right after; never pulled, never converted, never in `benchmark.json` |
| printed | `warm-up:   <n> cases x <i> samples in <s>s, a pre-flight check, not measured; hottest <c> C before, <c> C after` |
| failure | `warning: WARM-UP FAILED, measuring anyway: <reason>`; the app is force-stopped and the session goes on |
| off | `iterations: 0` |
| cost | one process: about 2 s of start, the plan's preparation, and about 1 s per case at 10 samples |

## One process per case

`run.isolation` ([config.md](../modules/config/docs/config.md)) decides how `CryptoBenchmark` runs; the run prints one line saying which.

| `run.isolation` | printed | what runs |
|---|---|---|
| `case` (default) | `measure:   one process per case (<n> cases, isolation: case)` | `-e log true` lists the planned timed cases without running them, then one `am instrument -e case <id>` per case; each process writes its own `benchmarkData.json`, pulled after it to `cases/<id>.json` in the process folder and kept; the process's `benchmarkData.json` is merged from those files once every case ran (the first case's `context`, every case's `benchmarks`, in run order) |
| `run` | `measure:   one process for every case (isolation: run)` | one `am instrument` holding every timed case |

- Progress: after each case `case:      <n> of <m> <id> ok` or `... failed`.
- `cases/`: emptied when a process starts; a stopped run keeps the files of the cases it finished.
- Device time: a process per case costs about 1 to 2 s of instrumentation start plus the plan's preparation on the device, per case and per pass.

- Why: a provider that leaks native memory across calls can abort its process (seen: a bundled provider's HMAC throwing `std::bad_alloc` after many `doFinal` calls on one reused `Mac`). In one process that ends every case after it; with a process per case the OS reclaims the memory when the case's process exits, and only that case is lost.
- Cost: each case pays an instrumentation start, about 1–2 s against about 60 s of measuring, and the device prepares the whole plan again in every process (`DevicePlan` has no per-case preparation), so a plan whose keys are slow to generate pays that per case too.
- A case whose process fails (`Process crashed.`, a failed test, no `benchmarkData.json`) or passes the `case` ceiling ([Timeouts](run.md#timeouts); the app is force-stopped before the next case) prints `case_failed: <id>: <reason>`, goes to `manifest.yaml` `problems`, and the run goes on; every case failing raises.
- `isolation: run`: `CryptoBenchmark` partial failures become warnings; all failed raises.
- Energy: the rails pre-flight runs once per run, after the plan push and AOT compile, never per process; `measured` keeps one Jetpack trace per case either way; `EnergyDryBenchmark`, `ScopedBenchmark`, `InteropCheck` and `DeviceProbe` stay one process each.

