# Device session

How a `--device` run measures: one session, its passes, its processes. Flags and steps: [run.md](run.md).

## Session

`lib/cryptobench/cryptobench/stages/measurement/session/measure.py` runs every measuring session on a device, for the benchmark (`CryptoBenchmark`); it gives only its plan: the test class, the cases, how a process's files are pulled and converted.

| step | what runs |
|---|---|
| session | `processRepetitions` processes (folders `process-<n>/` when above 1) in blocks of `run.resumeBlockRuns`, each finished block recorded and a recorded one kept by a resumed run ([results.md](results.md#resuming-a-stopped-run)), merged by `MergeRunsKt`; a case whose processes hold unequal run counts of a metric is not merged (`not_merged: <id>: unequal_samples: ...`), and a runtime value another process reports differently is one `runtime_differs: <key>: ...` line, the first kept |
| process | clear the device's outputs; one `am instrument` per case; pull `benchmarkData.json`, the plan files, `cpu-pins.yaml`; convert with `ConvertKt` |
| hooks | around the session, each process and each case: the cool-down (`lib/cryptobench/cryptobench/stages/measurement/session/cooldown_hook.py`), the clock state (`lib/cryptobench/cryptobench/stages/measurement/session/clocks_hook.py`), the energy window (`lib/cryptobench/cryptobench/stages/measurement/session/energy_hook.py`), the temperature with the thermal gate's history (`lib/cryptobench/cryptobench/stages/measurement/session/thermal_hook.py`, `lib/cryptobench/cryptobench/stages/measurement/session/gate_history.py`, [Thermal gate](#thermal-gate)); the gate itself is held only by the launch loop |
| a case hook fails | an `Exception` in a hook's `before_case` or `after_case` costs that case only: `case_failed: <id>: hook_failed: <Hook>.<step>: <Type>: <message>` in `problems`, the case left out of the process's data; a failed `before_case` starts no instrumentation, the hooks that started it still run `after_case` |
| a process hook fails to start | the hooks whose `before_process` ran, the failing one included, are abandoned in reverse (the energy window closes); the error ends the run as before |
| a process hook fails to close | every other hook's `after_process` still runs (later failures print `warning: hook_failed: ...`), the pulled data is converted to `benchmark.json`, then the first error ends the run |
| Ctrl-C, SIGTERM, SIGHUP | the signals map to Ctrl-C (`shared/stop/child.py` `stop_like_ctrl_c`; SIGHUP where the platform has it); the interrupt kills `adb`, not the test it started, so the session force-stops the app on the device before abandoning the hooks; the run then ends as an interrupt |
| lost device | [Lost device](#lost-device) |
| any stop inside a process | after the hooks are abandoned, `prepared.yaml`, `skipped.yaml` and `cpu-pins.yaml` are pulled once more (a failed pull: `warning: plan_not_pulled: ...`); the process's `case_failed` lines join `problems`; the manifest is written marked `partial` ([results.md](results.md#manifestyaml)) |

## Lost device

`lib/cryptobench/cryptobench/shared/device/adb.py` turns any adb call whose output names a lost transport (`device unauthorized`, `device offline`, `device '<serial>' not found`, `no devices/emulators found`, `error: closed`, adb server errors), and any adb call that exits non-zero, or an `am instrument` that did not pass, while `adb get-state` no longer says `device`, into `device_lost: adb <command>: <reason>`.

| rule | value |
|---|---|
| printed at measurement start | `device:    a lost adb transport is waited for up to <m> min, adb get-state every <s> s` |
| in a case | never a failed case: `lib/cryptobench/cryptobench/shared/device/reconnect.py` polls `adb get-state` until it says `device`, then the same case is held by the gate and launched again; its retries and discards are unchanged |
| outside a case | the step (output clear, case listing, plan pull, a hook's process step, plan push, gate start, warm-up) runs again once the device is back |
| past the bound | `device_lost: <reason>; not back after <s> s (adb get-state: <state>); run stopped`: the hooks close without waiting again, the cases measured so far stay, the manifest is marked `partial`, the run exits 1 |
| one instrumentation step | `DeviceProbe`, `EndToEndCheck`, `InteropCheck`, `ScopedInterop` and the energy dry pass run through `lib/cryptobench/cryptobench/shared/device/instrumentation.py` `run()`: once the device is back the whole step runs again, its clears first; their plan push waits the same way |
| pass rule | `DeviceProbe`, `InteropCheck`, `ScopedInterop` and a measured case pass only on an `OK (1 test)` line; `EndToEndCheck`, the energy dry pass and the warm-up on any `OK (<n> tests)` line |
| discovery | install and configure do not wait: a lost device there ends the run |

## Passes

`run.passes` ([config.md](../apps/benchmark/modules/config/docs/config.md)) splits a device run into one session per metric group; without it one pass measures every metric.

| pass | measures | samples | energy |
|---|---|---|---|
| `timing` | `TIME` | `samples` override every `iterations` | none: no window, no trace pulled |
| `energy` | `TIME` (dropped at the merge) and `energyJ` | `samples` set the timed phase, which is the energy window (`windowSeconds` applies only to `dry`); a short window sizes the case once per run, so every process holds equal samples ([energy.md](energy.md#capture-modes)) | the case's own capture (`measured`); rails pre-flight once per run |
| `allocation` | `ALLOCATION`, one run per sample (`SampledAllocations` inside the timed phase; androidx's own phase keeps its 5) | as `timing` | none |

- Per group: timing takes many short samples with no trace pulled; energy takes a window of about 100 rail polls; allocation counting slows the timed loop, and those times never reach the results.
- Merge: the timing pass's rows are the base, or with a single pass that pass's own (an energy-only run's time comes from its uncleaned samples; latency is read from a timing run); `MergePassesKt` takes `energyJ` only from the energy pass and `allocationCount` only from the allocation pass. A case a pass lost has no value of that metric (`not_merged: <id>: <key>: its pass has no row`), never the timing pass's, so every value of one metric comes from one pass and drift between passes never enters a ratio.
- Layout: `benchmark/<pass>/` (with `process-<n>/` under it), then `benchmark/benchmark.json` merged; with repetitions also `benchmark/process-<n>/benchmark.json`, the n-th process of every pass merged, which `manifest.yaml` lists as `processes`.
- Each pass prints `pass:      <name> pass: <n> processes, <time> on the device`; the run's device time is their sum, plus thermal sleeps.
- `capture: dry` with `run.passes` stops with `not_supported`; an energy pass with no `measured` case is skipped with a warning; `--bench` warns and measures once per process.

## Variants

Each entry's `variants`, else `run.variants` ([operations.md](../apps/benchmark/modules/preparation/docs/operations.md#variants)): the device prepares one case per kept path of each item; `lib/cryptobench/cryptobench/stages/measurement/session/variant_order.py` orders the benchmark's cases, on a device and on the host.

| rule | value |
|---|---|
| order | the items shuffled per process with `Random("<orderSeed>:<repetition>")` (`run.orderSeed`, required); an item's `fixed` and `notFixed` cases adjacent, `fixed` first in odd repetitions and `notFixed` first in even ones (A/B, then B/A: A/B/B/A over two); a host run lists its cases once (`ListCasesKt`) and each `BenchKt` process measures them in its `order.txt` |
| item | the case id without its last part `_fixed`, `_notFixed` or `_secure`; a `secure` case is an item of its own (another provider) |
| process | each variant in its own process |
| inputs | message bytes from `run.seed`, equal for both; keys from unseeded `SecureRandom` per process, so they differ ([operations.md](../apps/benchmark/modules/preparation/docs/operations.md#variants)); setup, inputs and buffers before the timer |
| cost | about 2x the device cases of an item that has two variants; key generation has one |

## Temperature

`lib/cryptobench/cryptobench/stages/measurement/thermal.py` reads `adb shell dumpsys thermalservice`, which an unrooted shell may run (`/sys/class/thermal` can be denied to it); `lib/cryptobench/cryptobench/stages/measurement/session/thermal_hook.py` reads it before and after every process and every case.

| rule | value |
|---|---|
| sensors | every `Temperature{mValue, mType, mName, mStatus}` line, keyed by the HAL's `mName`; a value outside -60..200 C (the HAL's `-3.4e38` for unknown, `NaN`) is no reading |
| status | `Thermal Status: <n>`, 0 none to 6 shutdown |
| section | `Current temperatures from HAL:` (queried when dumpsys runs); when absent or empty, `Cached temperatures:` with note `source: cached` |
| unavailable | `start`, `end`, statuses null and the reason in `thermalNote`; the case is measured as ever |
| files | `thermal.json` per process folder (`process` and `cases`; with the gate on also its `gate` baseline (`sensors`, `kept`, `from`: the scope it held under) and each case's `gate`); `ConvertKt --thermal` puts each case's reading in `benchmark.json` ([results.md](results.md#benchmarkjson-case-fields)) |
| per pass | `thermal:   <pass>: skin <sensor> <c> C at a case start, <c> C at an end; CPU <c> C at a case start, <c> C at an end; <n> pauses, <s> s paused; <n> cases ended throttled (status > 0)`; skin is the gate's reading (live type-3 sensors), CPU the hottest live type-0 sensor, each the maximum over the pass's cases; a side with no reading prints `skin unavailable` or `CPU unavailable`, both `temperature unavailable: <note>`; other sensor types are in `thermal.json` only |
| cost | two `dumpsys` calls per case, under a second |
| Jetpack's heat pause | `run.thermalThrottleSleepSeconds` passed as `-e androidx.benchmark.thermalThrottle.sleepDurationSeconds` to every measuring process; unset keeps Jetpack's 90 s |

- Cached values: AOSP's `ThermalManagerService` fills `Cached temperatures` only from the HAL's `onTemperatureChanged` callbacks, which a HAL sends when a sensor's severity changes; between changes the cached value can be minutes old. The `Current temperatures from HAL` section asks the HAL at dump time. A dump to an unrooted shell may not carry that section; when it does not, every reading is noted `source: cached` and is a lower bound on how stale the temperature is.

## Cool-down and frequency caps

| rule | value |
|---|---|
| cool-down | `run.caseCooldownSeconds` (0), or the pass's own `run.passes.<p>.caseCooldownSeconds` when :config wrote one: the host sleeps before every measured case but each session's first, before the case's temperature and clocks are read; the device adds no rest to a measured case (`harness.energy.cooldownSeconds` is the dry pass's, [energy.md](energy.md#config-keys)) |
| printed | `cool-down: <pass>: <n> x <s> s = <t> s between cases` per pass when set |
| with the gate | the cool-down sleeps first, with the gate, the hold comes first ([Thermal gate](#thermal-gate)) |
| cost | `(cases - 1) x seconds` per pass; at 20 s and 50 cases about 16 min a pass |
| caps | `clocks.yaml` `cases`: per case the online cores whose `scaling_max_freq` is below `cpuinfo_max_freq` at its start and end; `clocks:    <n> of <m> cases started or ended with a core capped below its maximum` per process |
| what caps show | boundary snapshots, one sysfs read each (tens of ms); a cap that rose and fell inside a case is not seen; unrooted, a cap cannot be lifted, only recorded |
| pinning | `run.harness.cpu.core` (`<index>` or `big`) pins the measuring thread on both paths ([harness.md](../apps/benchmark/modules/android/docs/harness.md#core-pinning)); a failed pin is `cpu_pin_failed` in `cpu-pins.yaml` and a warning |

## Thermal gate

Why: the phone's power controller lowers the CPU limit once skin reaches its own threshold, 36 C on a Pixel 10. A run that crosses it measures two speeds.

| step | rule |
|---|---|
| on | `run.thermalGate` or a `run.passes.<p>.thermalGate` set; a `--device` run only. One gate (`dynamic_temperature.py`) for every pass, energy included: a pass that needs other values overrides keys of the same gate, never a second path |
| scope | a pass holds under `run.passes.<p>.thermalGate` when :config wrote one (merged key by key over `run.thermalGate`), else under `run.thermalGate`; the warm-up holds under `run.thermalGate`; a scope the run does not set is off. `effective_view.scoped` selects, never merges. One `TEMPERATURE GATE SET[ for <scope>]: ...` line per scope |
| startup | once, before the build: `lib/cryptobench/cryptobench/stages/measurement/thermal.py` `capability`: live type-3 (SKIN) sensors, or one reason. Anything else prints `TEMPERATURE SET BUT DEVICE CAN'T POLL` and the run goes on |
| start limit | `temperatureKeptCelsius` minus the start margin. `lib/cryptobench/cryptobench/stages/measurement/session/dynamic_temperature.py` is the facade; the arithmetic is in `lib/cryptobench/cryptobench/stages/measurement/start_margin.py` |
| hold | before every launch of a run, the warm-up and the energy dry pass: above the limit, wait `cooldownMinutes`, then read every `pollMinutes` |
| end | a run ending at or above `temperatureKeptCelsius` is discarded and measured again; the margin widens by `backoffFactor`, up to `maximumCelsius`; `cleanRunsToRecover` clean runs narrow it by `recoveryCelsius`, never below `initialCelsius` |
| stop | still too hot after `pollTerminateMinutes`: the benchmark stops with `temperature_gate_timeout` |
| limit | `discardLimit` discards of one run: `onDiscardLimit`, `nextCase` (the case fails, the next goes on) or `stop` (the benchmark stops); the vocabulary is `codes.yaml` `temperature_discard_limit` `values`, which :config's `ThermalGate.ON_DISCARD_LIMIT` matches (`test_thermal_gate.py`) |
| read | every gate key through `effective_view.required` when the gate opens: an absent one is `missing_field: <scope>.<key> in effective.yaml`, an unknown `onDiscardLimit` `invalid: <scope>.onDiscardLimit ...`, both before the first case |
| unreadable | a reading is retried `readRetries` times; still unreadable: logged, that run is dropped, the next case goes on; a failed reading is never a pass |
| refused | a failed launch whose case the device recorded in `skipped.yaml` with a code `codes.yaml` holds as an `outcome` or an `error` (`keystore_unsupported`, `strongbox_unavailable`, `api_too_low`, `not_supported`, ...): `case_skipped: <id>: <code>` in `problems`, not launched again in that process; a record without such a code, or none, is an other failure |
| all skipped | a process whose every case is `case_skipped`, or a case listing (the warm-up's or a process's) the plan check refused with every case in `skipped.yaml` a final skip: `all_cases_skipped: ...`, the run stops measuring, its manifest keeps `prepared.yaml` and `skipped.yaml` and no `benchmark.json`, exit 0; a session's row for it is `all_skipped` ([sessions.md](sessions.md)) |
| other failures | crash, timeout, a result rule's fail ([validation.md](validation.md#case-rules)): `launchRetries` more launches, then the next case |
| order | hold, then the case hooks, launch, hooks, verdict (`lib/cryptobench/cryptobench/stages/measurement/session/launch.py`) |

## Warm-up

`run.warmup` ([config.md](../apps/benchmark/modules/config/docs/config.md)): one process before the first pass of a `--device` benchmark run.

| rule | value |
|---|---|
| what it is | a pre-flight check that the app, the providers and the timed loop run on this device; not temperature stabilisation, and no number of it is kept |
| cases | `jobs`: test-set rules, resolved by config to the entries they select; `[]` the plan's first `run.warmup.cases` (3); a case `skipped.yaml` holds as a final skip is left out, and a warm-up whose only failures are such skips prints `warm-up:   case_skipped: <id>: <code>` per case and counts the rest, or chooses again when none is left |
| samples | `iterations` (10) per case, as `-e cryptobench.pass warmup`: no energy capture |
| output | deleted on the device right after; never pulled, never converted, never in `benchmark.json` |
| printed | `warm-up:   <n> cases x <i> samples in <s>s, a pre-flight check, not measured; skin <sensor> <c> C before, <c> C after; CPU <c> C before, <c> C after`, unavailable sides as per pass |
| failure | `warning: WARM-UP FAILED, measuring anyway: <reason>`; the app is force-stopped and the session goes on |
| off | `iterations: 0` |
| cost | one process: about 2 s of start, the plan's preparation, and about 1 s per case at 10 samples |

## One process per case

Each pulled case file is held against the result rules: [validation.md](validation.md).

`CryptoBenchmark` runs one instrumentation process per measured case.

| printed | what runs |
|---|---|
| `measure:   one process per case (<n> cases)` | `-e log true` lists the planned timed cases without running them, then one `am instrument -e case <id>` per case; each process writes its own `benchmarkData.json`, pulled after it to `cases/<id>.json` in the process folder and kept; the process's `benchmarkData.json` is merged from those files again after each case that passed (the first case's `context`, every case's `benchmarks`, in run order) |

- Order: `order:     <process folder>/order.txt`, the cases in the order this process launches them, one id per line, written before the first launch; a host process writes one too, before its `BenchKt` starts, and keeps no `cases/`.
- Progress: after each case `case:      <n> of <m> <id> ok` or `... failed`.
- `cases/`: empty when a process starts, since the run's publish moved an earlier unit aside ([results.md](results.md#device-folder)); a stopped run keeps the files of the cases it finished, and `benchmarkData.json` holds them all.
- Device time: a process per case costs about 1 to 2 s of instrumentation start plus the plan's preparation on the device, per case and per pass.

- Why: a provider that leaks native memory across calls can abort its process (seen: a bundled provider's HMAC throwing `std::bad_alloc` after many `doFinal` calls on one reused `Mac`). In one process that ends every case after it; with a process per case the OS reclaims the memory when the case's process exits, and only that case is lost.
- Cost: each case pays an instrumentation start, about 1–2 s against about 60 s of measuring, and the device lists the plan again in every process without calling a provider, then prepares only its own case.
- A case whose process fails (`Process crashed.`, a failed test, no `benchmarkData.json`) or passes the `case` ceiling ([Timeouts](timeouts.md); the app is force-stopped before the next case) prints `case_failed: <id>: <reason>`, goes to `manifest.yaml` `problems`, and the run goes on; every case failing raises, unless every one is `case_skipped` ([Thermal gate](#thermal-gate) table, `all skipped`).
- Energy: the rails pre-flight runs once per run, after the plan push and AOT compile, never per process; `measured` keeps one Jetpack trace per case; `EnergyDryBenchmark`, `ScopedInterop`, `InteropCheck` and `DeviceProbe` stay one process each.
