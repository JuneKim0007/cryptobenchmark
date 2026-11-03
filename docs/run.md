# Run

## Prerequisites

| need | value |
|---|---|
| Java | 17 toolchain target; Kotlin comes from the Gradle plugin `kotlin("jvm")` 2.2.21 |
| host Python deps | `scripts/requirements.txt`: PyYAML>=6, matplotlib>=3.7 |
| energy Python deps | `tools/energy/requirements.txt`, see [energy.md](energy.md) |
| `ANDROID_HOME` (`--device`) | default `~/Library/Android/sdk`; adb at `$ANDROID_HOME/platform-tools/adb` |
| device state (`--device`) | `adb get-state` must print `device` |
| `ANDROID_SERIAL` (`--device`) | selects one device; several attached and none selected stops with `several_devices`; a serial not attached stops with `device_not_attached` |
| root (`--device`) | not required: the app creates its own files directory; shell reads it through group `ext_data_rw` |

## scripts/pipeline.py

```
python3 scripts/pipeline.py [--config PATH] [--results DIR] [--discovery overwrite|keep|reuse]
                            [--bench | --device] [--suppress-errors ERRORS] [--energy-python PYTHON]
                            [--energy-accept-unresponsive] [--stacktrace] [--stream] [--harness HARNESS_YAML]
                            [--interop PLAN_YAML] [--probe] [--identify]
```

| flag | default | effect |
|---|---|---|
| `--config PATH` | `$CRYPTOBENCH_CONFIG`, then `~/.config/cryptobench/global.yaml`, then `config/global.yaml` | the `global.yaml` to run |
| `--results DIR` | `<repo>/results` | results root; the run writes `<DIR>/<device_id>/` ([results.md](results.md#device-folder)) |
| `--discovery` | `overwrite` | `overwrite` clears `discovery/` first; `keep` adds a new capture; `reuse` keeps this device's capture, found by asking the JVM for its id first |
| `--bench` | off | also prepare, measure and analyse on the JVM via quick-bench |
| `--device` | off | probe, prepare and measure on the attached device over adb |
| `--probe` | off | discovery and configure only, with `--device` on the device; the device folder and its manifest, nothing measured |
| `--identify` | off | one line `identity:  {deviceId, mode, config, inputs}` (JSON) and nothing written: `getprop` on a device, `RuntimeFieldsKt` on a host; the id the probe would give |
| `--suppress-errors ERRORS` | `""` | passed as `androidx.benchmark.suppressErrors`, e.g. `EMULATOR,UNLOCKED`; numbers are then not comparable |
| `--energy-python PYTHON` | `sys.executable` | interpreter with `tools/energy/requirements.txt` installed; `requirements-manafa.txt` too for `energy.source: manafa` |
| `--energy-accept-unresponsive` | off | run energy cases on unresponsive rails, see [energy.md](energy.md#pre-flight) |
| `--stacktrace` | off | print the tool's full output on failure |
| `--stream` | off | show each tool's progress |
| `--harness HARNESS_YAML` | off | with `--device`: generate, install and measure perf-repair's scopes instead of the plan's cases, see [scoped.md](../modules/android/docs/scoped.md) |
| `--interop PLAN_YAML` | off | with `--bench` or `--device`: discover, then check perf-repair's `interop_plan.yaml` pairs instead of measuring, see [interop.md](../modules/preparation/docs/interop.md) |

| rule | result |
|---|---|
| `--bench` with `--device` | rejected (mutually exclusive) |
| `--device` with `--discovery reuse` | fails |
| `--suppress-errors` or `--energy-accept-unresponsive` without `--device` | fails |
| energy capture other than `none` without `--device` | fails |
| `--harness` without `--device` | fails |
| `--harness` with `--results` | fails: `measured/` goes beside `harness.yaml` |
| `--interop` without `--bench` or `--device`, or with `--harness` | fails |
| `--probe` or `--identify` with `--bench`, `--harness` or `--interop` | fails |
| `--probe`, or neither `--bench` nor `--device` | discover and configure only, then a manifest that replaces the device's last one |
| any failure | prints `error: <message>`, exits 1; an error with no code of its own is `subprocess_failed: <command> exited <n>` or `internal_error: <type>: <message>`, with the traceback under `--stacktrace` |

- Host discovery runs `ProbeKt`; `--discovery reuse` runs `RuntimeFieldsKt` first, then adds `--reuse`.
- The run's capture is the one its discovery wrote: on a host the file `ProbeKt` printed, on a device the one capture the probe added to `discovery/`; its trial is the file with the same stamp. With `--discovery keep` older captures stay beside it and are never picked by their stamp, which comes from the device clock.
- Device discovery runs `ConfigureKt` with `--facts`.
- `run.processRepetitions` ([config.md](../modules/config/docs/config.md)) above 1: runs merged with `MergeRunsKt`.
- Tool commands: [tools.md](tools.md). Output: [results.md](results.md).

## Timeouts

Every host subprocess runs under a ceiling from `scripts/timeouts.py`; past it the process is killed and the run stops with `error: timeout: <step> ran past <s> s: <command>`. A ceiling only catches a hang: each is several times the longest real step, and none is a setting.

| step | ceiling | covers | why this value |
|---|---|---|---|
| `adb` | 10 min | one adb command: shell, push, pull, AOT compile, Perfetto pre-flight | a pull of every case's Perfetto trace is the longest; `cmd package compile` takes under a minute |
| `install` | 60 min | root Gradle `installRelease` and `installReleaseAndroidTest` | a cold build with dependency download takes minutes |
| `case` | 60 min | one case's `am instrument` under `isolation: case` | one case measures for about a minute |
| `instrument` | 12 h | one `am instrument`: `CryptoBenchmark` with every case (`isolation: run`), `DeviceProbe`, `EnergyDryBenchmark`, `InteropCheck` | a device benchmark of the full test set at 400 samples with thermal sleeps takes hours |
| `gradle` | 4 h | a `tools/` Gradle run: probe, configure, host measure, convert, merge | the host measure of the full test set is the longest |
| `compile` | 30 min | `--harness` scope compile | one compile of the android test sources |
| `energy` | 2 h | `tools/energy` (`energy.py`, `preflight.py`), manafa's pre-flight and answer | the trace processor loads one trace per case |
| `analysis` | 30 min | `analyze.py`, `charts.py` | seconds in practice |

- An energy step past its ceiling is `energy_failed: timeout: ...` and the run goes on ([energy.md](energy.md#outputs)).
- Analysis runs `analyze.py`, then `charts.py` ([tools.md](tools.md#chartspy)).

## scripts/explain.py

```
python3 scripts/explain.py [--config PATH] [--results DIR] [--device-id ID]
```

- Prints the run id, each `run`, `policy` and `analysis` key of `<results>/<device_id>/configuration/effective.yaml` with its value and source: the global file when written there, else `default`.
- Ends with the entry count and the test set.
- A root with several device folders needs `--device-id`, else `several_device_results`.

## scripts/demo.sh

| flag | effect |
|---|---|
| none | `config/global-quick.yaml` (11 test-set entries, about 30 s), `results/demo/<device_id>`, `--discovery overwrite` |
| `--warm` | compile both tools, exit |
| `--fast` | `config/global-demo.yaml`: `testsets/smoke.yaml` (3 entries), `inputSizes [1024]`, about 8 s |
| `--reuse` | `--discovery reuse` |
| `--config FILE` | another `global.yaml` |
| `--results DIR` | another results root |
| `-h`, `--help` | usage |

- Runs `pipeline.py --bench --stream`, then prints the head of `results/demo/<device_id>/analysis/summary.md`.

## Device run

| step | command or path |
|---|---|
| install | root `gradlew :android:installRelease :android:installReleaseAndroidTest`, plus `-PbundledArtifacts=<artifact>,...` when global.yaml has `providers.bundled` |
| bundled providers | `DeviceProbe` gets `-e bundledProviders '<json>'`; after configure, `effective.yaml` `bundledProviders` must equal the built list, else `bundled_mismatch` |
| plan and androidx output directories | by API level: `modules/android/docs/harness.md#device-directories` |
| AOT compile | `cmd package compile -f -m speed` on both APKs |
| profiler | `-e androidx.benchmark.profiling.mode None` |
| pull | whole plan directory into `discovery/` |


### Device session

`scripts/measure_session.py` runs every measuring session on a device, for the benchmark (`CryptoBenchmark`) and the before/after run (`ScopedBenchmark`, [scoped.md](../modules/android/docs/scoped.md)); a path gives only its plan: the test class, the cases, how a process's files are pulled and converted.

| step | what runs |
|---|---|
| session | `processRepetitions` processes (folders `process-<n>/` when above 1), merged by `MergeRunsKt` |
| process | clear the device's outputs; one `am instrument` per case (`isolation: case`) or one for all (`run`); pull `benchmarkData.json`, the plan files and `cpu-pins.yaml`; convert with `ConvertKt` |
| hooks | around the session, each process and each case: the clock state and the energy window (`scripts/session_hooks.py`) |

### One process per case

`run.isolation` ([config.md](../modules/config/docs/config.md)) decides how `CryptoBenchmark` runs; the run prints one line saying which.

| `run.isolation` | printed | what runs |
|---|---|---|
| `case` (default) | `measure:   one process per case (<n> cases, isolation: case)` | `-e log true` lists the planned timed cases without running them, then one `am instrument -e case <id>` per case; each process writes its own `benchmarkData.json`, pulled after it and joined into one (the first process's `context`, every process's `benchmarks`) |
| `run` | `measure:   one process for every case (isolation: run)` | one `am instrument` holding every timed case |

- Why: a provider that leaks native memory across calls can abort its process (seen: a bundled provider's HMAC throwing `std::bad_alloc` after many `doFinal` calls on one reused `Mac`). In one process that ends every case after it; with a process per case the OS reclaims the memory when the case's process exits, and only that case is lost.
- Cost: each case pays an instrumentation start, about 1–2 s against about 60 s of measuring, and the device prepares the whole plan again in every process (`DevicePlan` has no per-case preparation), so a plan whose keys are slow to generate pays that per case too.
- A case whose process fails (`Process crashed.`, a failed test, no `benchmarkData.json`) or passes the `case` ceiling ([Timeouts](#timeouts); the app is force-stopped before the next case) prints `case_failed: <id>: <reason>`, goes to `manifest.yaml` `problems`, and the run goes on; every case failing raises.
- `isolation: run`: `CryptoBenchmark` partial failures become warnings; all failed raises.
- Energy: the rails pre-flight runs once per run, before the plan is pushed, never per process; `measured` keeps one Jetpack trace per case either way; `EnergyDryBenchmark`, `ScopedBenchmark`, `InteropCheck` and `DeviceProbe` stay one process each.

### Recover a metric without a device

Androidx always runs its allocation phase, so `benchmarkData.json` holds `allocationCount` for every case even when `run.metrics` was `[TIME]`. Converting it again reports it; nothing runs on the device:

```
D=results/<device_id>
tools/jca-contract/gradlew -p tools/quick-bench run -q -PmainClass=ConvertKt \
  --args="$D/benchmark/benchmarkData.json $D/preparation/prepared.yaml $D/benchmark $D/benchmark/energy.json --metrics=TIME,ALLOCATION"
```

- Leave `energy.json` out when the run captured no energy.
- With `run.processRepetitions` above 1: once per `process-N/`, then `MergeRunsKt`.
- Then rerun `python3 -m perfrepair.data_handler.inbound --device-results "$D"`; its digests see the new `benchmark.json`.

## Device facts

| fact | rule |
|---|---|
| `rooted` | `su -c id` returns `uid=0` within 5 s |
| `pinning` | release APK contains `lib/<abi>/libaffinity.so` |
| ABI | `pm dump` `primaryCpuAbi`, else `ro.product.cpu.abi` |
| `cpuLocked` | every online core has `scaling_min_freq == scaling_max_freq` before and after the measure; unreadable gives `unknown` |
